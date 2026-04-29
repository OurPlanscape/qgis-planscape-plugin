import json

from planscape.services import auth_service


def test_sign_in_request_logs_api_call(monkeypatch):
    logs = []
    base_url = "https://dev.planscape.org/planscape-backend"

    def fake_post(url: str, data: dict[str, str] | None = None) -> str:
        del url, data
        return json.dumps({"access": "access-token", "refresh": "refresh-token"})

    monkeypatch.setattr(auth_service.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(auth_service, "post", fake_post)

    auth_service.sign_in_request("person@example.com", "secret", base_url)

    assert logs == [f"[API] POST:{base_url}/dj-rest-auth/login/"]
