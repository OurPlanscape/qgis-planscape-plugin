from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsProcessingException, QgsSettings

from planscape.api.auth import AuthApiError, sign_in_request
from planscape.qgis_plugin_tools.tools.resources import plugin_name

T = TypeVar("T")

ENVIRONMENT_URLS: dict[str, str] = {
    "dev": "https://dev.planscape.org/planscape-backend",
    "staging": "https://staging.planscape.org/planscape-backend",
    "catalog": "https://catalog.planscape.org/planscape-backend",
    "production": "https://app.planscape.org/planscape-backend",
}
DEFAULT_ENVIRONMENT = "catalog"
LOGIN_PATH = "/dj-rest-auth/login/"

ENVIRONMENT_SETTING_KEY = "auth/environment"
EMAIL_SETTING_KEY = "auth/email"
CREDENTIALS_AUTHCFG_KEY = "auth/credentials_authcfg"
TOKEN_AUTHCFG_KEY = "auth/token_authcfg"  # noqa: S105
AUTH_REQUIRED_MESSAGE = "Planscape authentication is required. Open the Planscape plugin and sign in first."


def get_setting(key: str, default: T, expected_type: Any) -> T:
    value = QgsSettings().value(f"{plugin_name()}/{key}", default)
    if value is None:
        return default
    return expected_type(value)


def set_setting(key: str, value: object) -> None:
    QgsSettings().setValue(f"{plugin_name()}/{key}", value)


class PlanscapeAuthError(Exception):
    pass


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    refresh_token: str


def environment_names() -> list[str]:
    return list(ENVIRONMENT_URLS)


def get_environment() -> str:
    environment = str(get_setting(ENVIRONMENT_SETTING_KEY, DEFAULT_ENVIRONMENT, str))
    if environment not in ENVIRONMENT_URLS:
        return DEFAULT_ENVIRONMENT
    return environment


def set_environment(environment: str) -> None:
    if environment not in ENVIRONMENT_URLS:
        message = f"Unsupported environment: {environment}"
        raise PlanscapeAuthError(message)
    set_setting(ENVIRONMENT_SETTING_KEY, environment)


def get_base_url(environment: str | None = None) -> str:
    resolved_environment = environment or get_environment()
    try:
        return ENVIRONMENT_URLS[resolved_environment]
    except KeyError as exc:
        message = f"No Planscape base URL configured for environment '{resolved_environment}'"
        raise PlanscapeAuthError(message) from exc


def login_url(environment: str | None = None) -> str:
    return f"{get_base_url(environment)}{LOGIN_PATH}"


def get_saved_email() -> str:
    return str(get_setting(EMAIL_SETTING_KEY, "", str))


def set_saved_email(email: str) -> None:
    set_setting(EMAIL_SETTING_KEY, email)


def get_token_authcfg_id() -> str:
    return str(get_setting(TOKEN_AUTHCFG_KEY, "", str))


def is_authenticated() -> bool:
    authcfg_id = get_token_authcfg_id()
    if not authcfg_id:
        return False
    return _load_auth_config(authcfg_id) is not None


def ensure_authenticated() -> str:
    authcfg_id = get_token_authcfg_id()
    if authcfg_id and _load_auth_config(authcfg_id) is not None:
        return authcfg_id

    raise QgsProcessingException(AUTH_REQUIRED_MESSAGE)


def sign_in(email: str, password: str, environment: str) -> LoginResult:
    if not email.strip():
        message = "Email is required."
        raise PlanscapeAuthError(message)
    if not password:
        message = "Password is required."
        raise PlanscapeAuthError(message)

    try:
        tokens = sign_in_request(email.strip(), password, get_base_url(environment))
    except AuthApiError as exc:
        raise PlanscapeAuthError(str(exc)) from exc

    set_environment(environment)
    set_saved_email(email.strip())

    credentials_authcfg_id = _upsert_basic_auth_config(email.strip(), password, environment)
    token_authcfg_id = _upsert_token_auth_config(tokens.access_token, environment)

    set_setting(CREDENTIALS_AUTHCFG_KEY, credentials_authcfg_id)
    set_setting(TOKEN_AUTHCFG_KEY, token_authcfg_id)

    return LoginResult(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


def sign_out() -> None:
    token_authcfg_id = get_token_authcfg_id()
    if token_authcfg_id:
        _remove_auth_config(token_authcfg_id)
    set_setting(TOKEN_AUTHCFG_KEY, "")


def _auth_manager():
    return QgsApplication.authManager()


def _load_auth_config(authcfg_id: str, *, full: bool = False) -> QgsAuthMethodConfig | None:
    if not authcfg_id:
        return None

    config = QgsAuthMethodConfig()
    ok, loaded_config = _auth_manager().loadAuthenticationConfig(authcfg_id, config, full)
    if not ok or not loaded_config.isValid():
        return None
    return loaded_config


def _remove_auth_config(authcfg_id: str) -> None:
    _auth_manager().removeAuthenticationConfig(authcfg_id)


def _upsert_basic_auth_config(email: str, password: str, environment: str) -> str:
    authcfg_id = str(get_setting(CREDENTIALS_AUTHCFG_KEY, "", str))
    config = _load_auth_config(authcfg_id, full=True) or QgsAuthMethodConfig("Basic")
    config.setMethod("Basic")
    config.setName(f"{plugin_name()} {environment} credentials")
    config.setUri(get_base_url(environment))
    config.setConfig("username", email)
    config.setConfig("password", password)
    return _save_auth_config(config, authcfg_id)


def _upsert_token_auth_config(access_token: str, environment: str) -> str:
    authcfg_id = str(get_setting(TOKEN_AUTHCFG_KEY, "", str))
    config = _load_auth_config(authcfg_id, full=True) or QgsAuthMethodConfig("APIHeader")
    config.setMethod("APIHeader")
    config.setName(f"{plugin_name()} {environment} bearer token")
    config.setUri(get_base_url(environment))
    config.clearConfigMap()
    config.setConfig("Authorization", f"Bearer {access_token}")
    return _save_auth_config(config, authcfg_id)


def _save_auth_config(config: QgsAuthMethodConfig, authcfg_id: str) -> str:
    if authcfg_id and config.id() == "":
        config.setId(authcfg_id)

    if authcfg_id:
        if not _auth_manager().updateAuthenticationConfig(config):
            message = "Could not update the saved Planscape credentials."
            raise PlanscapeAuthError(message)
        return authcfg_id

    ok, stored_config = _auth_manager().storeAuthenticationConfig(config)
    if not ok or not stored_config.id():
        message = "Could not save the Planscape credentials to QGIS."
        raise PlanscapeAuthError(message)
    return stored_config.id()
