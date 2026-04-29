import pytest
from qgis.core import QgsProcessingException, QgsSettings
from qgis.PyQt.QtWidgets import QLineEdit

from planscape import auth
from planscape.gui.auth_dialog import AuthDialog
from planscape.processing.import_raster import ImportRasterAlgorithm
from planscape.processing.import_vector import ImportVectorAlgorithm
from planscape.qgis_plugin_tools.tools.resources import plugin_name
from planscape.services.auth_service import AuthServiceError, LoginTokens


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
    assert captured == {
        "email": "person@example.com",
        "password": "secret",
        "base_url": "https://staging.planscape.org/planscape-backend",
    }


def test_sign_in_wraps_auth_service_errors(monkeypatch):
    _clear_auth_settings()

    def fake_sign_in_request(email: str, password: str, base_url: str) -> LoginTokens:
        del email, password, base_url
        message = "Planscape returned an invalid login response."
        raise AuthServiceError(message)

    monkeypatch.setattr(auth, "sign_in_request", fake_sign_in_request)

    with pytest.raises(auth.PlanscapeAuthError, match="invalid login response"):
        auth.sign_in("person@example.com", "secret", "catalog")


def test_sign_in_does_not_save_auth_configs_when_service_fails(monkeypatch):
    _clear_auth_settings()
    calls = []

    def fake_sign_in_request(email: str, password: str, base_url: str) -> LoginTokens:
        del email, password, base_url
        message = "Planscape login did not return an access token."
        raise AuthServiceError(message)

    monkeypatch.setattr(auth, "sign_in_request", fake_sign_in_request)
    monkeypatch.setattr(auth, "_upsert_basic_auth_config", lambda *args: calls.append(args))

    with pytest.raises(auth.PlanscapeAuthError, match="access token"):
        auth.sign_in("person@example.com", "secret", "catalog")
    assert calls == []


def test_sign_out_clears_token_authcfg_and_removes_saved_token(monkeypatch):
    _clear_auth_settings()
    removed = []
    auth.set_setting(auth.TOKEN_AUTHCFG_KEY, "token-authcfg")

    monkeypatch.setattr(auth, "_remove_auth_config", removed.append)

    auth.sign_out()

    assert removed == ["token-authcfg"]
    assert auth.get_token_authcfg_id() == ""


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
