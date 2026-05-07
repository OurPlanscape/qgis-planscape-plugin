import json

import pytest

from planscape.api import auth
from planscape.api.exceptions import AuthApiError
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException


def test_sign_in_request_logs_api_call(monkeypatch):
    logs = []
    base_url = "https://dev.planscape.org/planscape-backend"

    def fake_post(url: str, data: dict[str, str] | None = None) -> str:
        del url, data
        return json.dumps({"access": "access-token", "refresh": "refresh-token"})

    monkeypatch.setattr(auth.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(auth, "post", fake_post)

    auth.sign_in_request("person@example.com", "secret", base_url)

    assert logs == [f"[API] SUCCESS:POST:{base_url}/dj-rest-auth/login/"]


def test_sign_in_request_logs_api_failure(monkeypatch):
    logs = []
    base_url = "https://dev.planscape.org/planscape-backend"

    def fake_post(url: str, data: dict[str, str] | None = None) -> str:
        del url, data
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(auth.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(auth, "post", fake_post)

    with pytest.raises(AuthApiError, match="failed"):
        auth.sign_in_request("person@example.com", "secret", base_url)

    assert logs == [f"[API] FAILED:POST:{base_url}/dj-rest-auth/login/:failed"]
