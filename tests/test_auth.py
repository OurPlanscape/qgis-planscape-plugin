import pytest
from qgis.core import QgsProcessingException, QgsSettings
from qgis.PyQt.QtWidgets import QLineEdit

from planscape import auth
from planscape.api.auth import AuthApiError, LoginTokens
from planscape.gui.auth_dialog import AuthDialog
from planscape.processing.import_raster import ImportRasterAlgorithm
from planscape.processing.import_vector import ImportVectorAlgorithm
from planscape.qgis_plugin_tools.tools.resources import plugin_name


def _clear_auth_settings() -> None:
    settings = QgsSettings()
    settings.remove(f"/{plugin_name()}/auth")


def test_default_environment_is_catalog():
    _clear_auth_settings()

    assert auth.get_environment() == "catalog"


def test_login_url_uses_environment_base_url():
    assert auth.login_url("production") == ("https://app.planscape.org/planscape-backend/dj-rest-auth/login/")


def test_auth_dialog_defaults(qgis_app):
    _clear_auth_settings()
    assert qgis_app is not None

    dialog = AuthDialog()

    assert dialog.environment_combo.currentText() == "catalog"
    assert dialog.email_input.text() == ""
    assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Password


def test_sign_in_stores_environment_and_authcfg_ids(monkeypatch):
    _clear_auth_settings()
    auth.set_setting(auth.AUTO_LOGIN_DISABLED_KEY, True)

    captured = {}

    def fake_sign_in_request(email: str, password: str, base_url: str) -> LoginTokens:
        captured["email"] = email
        captured["password"] = password
        captured["base_url"] = base_url
        return LoginTokens(access_token="access-token", refresh_token="refresh-token")

    def fake_upsert_basic(email: str, password: str, environment: str) -> str:
        assert email == "person@example.com"
        assert password == "secret"
        assert environment == "staging"
        return "basic-authcfg"

    def fake_upsert_token(access_token: str, environment: str) -> str:
        assert access_token == "access-token"
        assert environment == "staging"
        return "token-authcfg"

    monkeypatch.setattr(auth, "sign_in_request", fake_sign_in_request)
    monkeypatch.setattr(auth, "_upsert_basic_auth_config", fake_upsert_basic)
    monkeypatch.setattr(auth, "_upsert_token_auth_config", fake_upsert_token)

    result = auth.sign_in("person@example.com", "secret", "staging")

    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"
    assert auth.get_environment() == "staging"
    assert auth.get_saved_email() == "person@example.com"
    assert str(auth.get_setting(auth.CREDENTIALS_AUTHCFG_KEY, "", str)) == "basic-authcfg"
    assert auth.get_token_authcfg_id() == "token-authcfg"
    assert auth.is_auto_login_disabled() is False
    assert captured == {
        "email": "person@example.com",
        "password": "secret",
        "base_url": "https://staging.planscape.org/planscape-backend",
    }


def test_sign_in_wraps_auth_api_errors(monkeypatch):
    _clear_auth_settings()

    def fake_sign_in_request(email: str, password: str, base_url: str) -> LoginTokens:
        del email, password, base_url
        message = "Planscape returned an invalid login response."
        raise AuthApiError(message)

    monkeypatch.setattr(auth, "sign_in_request", fake_sign_in_request)

    with pytest.raises(auth.PlanscapeAuthError, match="invalid login response"):
        auth.sign_in("person@example.com", "secret", "catalog")


def test_sign_in_does_not_save_auth_configs_when_api_fails(monkeypatch):
    _clear_auth_settings()
    calls = []

    def fake_sign_in_request(email: str, password: str, base_url: str) -> LoginTokens:
        del email, password, base_url
        message = "Planscape login did not return an access token."
        raise AuthApiError(message)

    monkeypatch.setattr(auth, "sign_in_request", fake_sign_in_request)
    monkeypatch.setattr(auth, "_upsert_basic_auth_config", lambda *args: calls.append(args))

    with pytest.raises(auth.PlanscapeAuthError, match="access token"):
        auth.sign_in("person@example.com", "secret", "catalog")
    assert calls == []


def test_token_auth_config_uses_qgis_api_header_shape(monkeypatch):
    captured = {}

    def fake_save_auth_config(config, authcfg_id: str) -> str:
        captured["authcfg_id"] = authcfg_id
        captured["method"] = config.method()
        captured["uri"] = config.uri()
        captured["config"] = config.configMap()
        return "token-authcfg"

    def fake_load_auth_config(authcfg_id: str, *, full: bool = False) -> None:
        del authcfg_id, full

    monkeypatch.setattr(auth, "_load_auth_config", fake_load_auth_config)
    monkeypatch.setattr(auth, "_save_auth_config", fake_save_auth_config)

    assert auth._upsert_token_auth_config("access-token", "catalog") == "token-authcfg"
    assert captured == {
        "authcfg_id": "",
        "method": "APIHeader",
        "uri": "https://catalog.planscape.org/planscape-backend",
        "config": {"header": "Authorization", "value": "Bearer access-token"},
    }


def test_is_authenticated_rejects_legacy_authorization_config(monkeypatch):
    _clear_auth_settings()

    class LegacyConfig:
        def method(self):
            return "APIHeader"

        def config(self, key: str):
            return {"Authorization": "Bearer access-token"}.get(key, "")

    def fake_load_auth_config(authcfg_id: str, *, full: bool = False) -> LegacyConfig:
        del authcfg_id, full
        return LegacyConfig()

    auth.set_setting(auth.TOKEN_AUTHCFG_KEY, "token-authcfg")
    monkeypatch.setattr(auth, "_load_auth_config", fake_load_auth_config)

    assert auth.is_authenticated() is False


def test_sign_out_clears_token_authcfg_and_removes_saved_token(monkeypatch):
    _clear_auth_settings()
    removed = []
    auth.set_setting(auth.TOKEN_AUTHCFG_KEY, "token-authcfg")

    monkeypatch.setattr(auth, "_remove_auth_config", removed.append)

    auth.sign_out()

    assert removed == ["token-authcfg"]
    assert auth.get_token_authcfg_id() == ""
    assert auth.is_auto_login_disabled() is True


def test_restore_authenticated_session_uses_saved_credentials(monkeypatch):
    _clear_auth_settings()
    auth.set_environment("staging")
    state = {"authenticated": False}
    captured = {}

    def fake_sign_in(email: str, password: str, environment: str) -> None:
        captured["email"] = email
        captured["password"] = password
        captured["environment"] = environment
        state["authenticated"] = True

    def fake_load_saved_credentials(environment: str) -> tuple[str, str]:
        del environment
        return "person@example.com", "secret"

    monkeypatch.setattr(auth, "is_authenticated", lambda: state["authenticated"])
    monkeypatch.setattr(auth, "_load_saved_credentials", fake_load_saved_credentials)
    monkeypatch.setattr(auth, "sign_in", fake_sign_in)

    assert auth.restore_authenticated_session() is True
    assert captured == {"email": "person@example.com", "password": "secret", "environment": "staging"}


def test_restore_authenticated_session_returns_false_without_saved_credentials(monkeypatch):
    _clear_auth_settings()
    removed = []

    def fake_load_saved_credentials(environment: str) -> None:
        del environment

    monkeypatch.setattr(auth, "_load_saved_credentials", fake_load_saved_credentials)
    monkeypatch.setattr(auth, "_remove_auth_config", removed.append)

    assert auth.restore_authenticated_session() is False
    assert auth.get_token_authcfg_id() == ""
    assert removed == []


def test_restore_authenticated_session_clears_token_when_saved_login_fails(monkeypatch):
    _clear_auth_settings()
    removed = []
    auth.set_setting(auth.TOKEN_AUTHCFG_KEY, "token-authcfg")

    def fail_sign_in(email: str, password: str, environment: str) -> None:
        del email, password, environment
        message = "Bad credentials"
        raise auth.PlanscapeAuthError(message)

    def fake_load_auth_config(*args, **kwargs) -> None:
        del args, kwargs

    def fake_load_saved_credentials(environment: str) -> tuple[str, str]:
        del environment
        return "person@example.com", "secret"

    monkeypatch.setattr(auth, "_load_auth_config", fake_load_auth_config)
    monkeypatch.setattr(auth, "_load_saved_credentials", fake_load_saved_credentials)
    monkeypatch.setattr(auth, "_remove_auth_config", removed.append)
    monkeypatch.setattr(auth, "sign_in", fail_sign_in)

    assert auth.restore_authenticated_session() is False
    assert auth.get_token_authcfg_id() == ""
    assert removed == ["token-authcfg"]


def test_dialog_sign_in_updates_status_and_clears_password(qgis_app, monkeypatch):
    _clear_auth_settings()
    assert qgis_app is not None

    calls = []
    accepted = {"value": False}

    def fake_sign_in(email: str, password: str, environment: str) -> None:
        calls.append((email, password, environment))

    monkeypatch.setattr(auth, "sign_in", fake_sign_in)
    monkeypatch.setattr(auth, "is_authenticated", lambda: True)

    dialog = AuthDialog()
    monkeypatch.setattr(dialog, "accept", lambda: accepted.__setitem__("value", True))
    dialog.email_input.setText("person@example.com")
    dialog.password_input.setText("secret")
    dialog.environment_combo.setCurrentText("production")

    dialog.sign_in_button.click()

    assert calls == [("person@example.com", "secret", "production")]
    assert dialog.password_input.text() == ""
    assert dialog.status_label.text() == "Authenticated for the production environment."
    assert dialog.sign_out_button.isEnabled() is True
    assert accepted["value"] is True


def test_dialog_sign_in_shows_error_on_auth_failure(qgis_app, monkeypatch):
    _clear_auth_settings()
    assert qgis_app is not None

    def raise_auth_error(email: str, password: str, environment: str) -> None:
        assert email == "person@example.com"
        assert password == "secret"
        assert environment == "catalog"
        message = "Bad credentials"
        raise auth.PlanscapeAuthError(message)

    monkeypatch.setattr(auth, "sign_in", raise_auth_error)
    monkeypatch.setattr(auth, "is_authenticated", lambda: False)

    dialog = AuthDialog()
    dialog.email_input.setText("person@example.com")
    dialog.password_input.setText("secret")

    dialog.sign_in_button.click()

    assert dialog.status_label.text() == "Bad credentials"
    assert dialog.password_input.text() == "secret"
    assert dialog.sign_in_button.isEnabled() is True


def test_dialog_sign_out_clears_password_and_disables_sign_out(qgis_app, monkeypatch):
    _clear_auth_settings()
    assert qgis_app is not None

    signed_out = {"value": False}

    def fake_sign_out() -> None:
        signed_out["value"] = True

    monkeypatch.setattr(auth, "sign_out", fake_sign_out)
    auth_state = {"value": True}
    monkeypatch.setattr(auth, "is_authenticated", lambda: auth_state["value"])

    dialog = AuthDialog()
    dialog.password_input.setText("secret")

    def fake_update_status() -> None:
        auth_state["value"] = False
        dialog.status_label.setText("Not authenticated. Sign in to the catalog environment.")
        dialog.sign_out_button.setEnabled(False)

    monkeypatch.setattr(dialog, "_update_status", fake_update_status)

    dialog.sign_out_button.click()

    assert signed_out["value"] is True
    assert dialog.password_input.text() == ""
    assert dialog.sign_out_button.isEnabled() is False


def test_import_raster_requires_authentication(monkeypatch):
    def raise_unauthenticated() -> None:
        raise QgsProcessingException(auth.AUTH_REQUIRED_MESSAGE)

    monkeypatch.setattr("planscape.processing.import_raster.ensure_authenticated", raise_unauthenticated)

    algorithm = ImportRasterAlgorithm()

    with pytest.raises(QgsProcessingException, match="sign in first"):
        algorithm.processAlgorithm({}, None, None)


def test_import_vector_requires_authentication(monkeypatch):
    def raise_unauthenticated() -> None:
        raise QgsProcessingException(auth.AUTH_REQUIRED_MESSAGE)

    monkeypatch.setattr("planscape.processing.import_vector.ensure_authenticated", raise_unauthenticated)

    algorithm = ImportVectorAlgorithm()

    with pytest.raises(QgsProcessingException, match="sign in first"):
        algorithm.processAlgorithm({}, None, None)


def test_import_algorithms_continue_when_authenticated(monkeypatch):
    raster_called = {"value": False}
    vector_called = {"value": False}

    def raster_ok() -> None:
        raster_called["value"] = True

    def vector_ok() -> None:
        vector_called["value"] = True

    monkeypatch.setattr("planscape.processing.import_raster.ensure_authenticated", raster_ok)
    monkeypatch.setattr("planscape.processing.import_vector.ensure_authenticated", vector_ok)

    assert ImportRasterAlgorithm().processAlgorithm({}, None, None) == {}
    assert ImportVectorAlgorithm().processAlgorithm({}, None, None) == {}
    assert raster_called["value"] is True
    assert vector_called["value"] is True
