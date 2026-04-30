import json

from planscape.api import auth


def test_sign_in_request_logs_api_call(monkeypatch):
    logs = []
    base_url = "https://dev.planscape.org/planscape-backend"

    def fake_post(url: str, data: dict[str, str] | None = None) -> str:
        del url, data
        return json.dumps({"access": "access-token", "refresh": "refresh-token"})

    monkeypatch.setattr(auth.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(auth, "post", fake_post)

    auth.sign_in_request("person@example.com", "secret", base_url)

    assert logs == [f"[API] POST:{base_url}/dj-rest-auth/login/"]
