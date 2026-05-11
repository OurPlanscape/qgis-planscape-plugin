import json

import pytest

from planscape.api import style
from planscape.api.exceptions import StyleAPIError, StylePayloadError
from planscape.models.api.style import CreateStyleRequest
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException

BASE_URL = "https://dev.planscape.org/planscape-backend"
AUTHCFG_ID = "authcfg-id"


def test_create_style_request_posts_admin_payload(monkeypatch):
    captured = {}

    def fake_post(url: str, authcfg_id: str = "", data: dict | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps({"id": 30, "name": "Smoke Style"})

    monkeypatch.setattr(style, "post", fake_post)

    result = style.create_style_request(
        BASE_URL,
        AUTHCFG_ID,
        CreateStyleRequest(
            name="Smoke Style",
            data={"map_type": "RAMP", "entries": []},
            organization=3,
            datalayers=[20],
        ),
    )

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/styles/",
        "authcfg_id": AUTHCFG_ID,
        "data": {
            "name": "Smoke Style",
            "type": "RASTER",
            "data": {"map_type": "RAMP", "entries": []},
            "organization": 3,
            "datalayers": [20],
        },
    }
    assert result.id == 30
    assert result.name == "Smoke Style"


def test_create_style_request_accepts_nested_style_response(monkeypatch):
    def fake_post(url: str, authcfg_id: str = "", data: dict | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"style": {"id": 30, "name": "Smoke Style"}})

    monkeypatch.setattr(style, "post", fake_post)

    result = style.create_style_request(
        BASE_URL,
        AUTHCFG_ID,
        CreateStyleRequest(name="Smoke Style", data={}, organization=3),
    )

    assert result.id == 30
    assert result.name == "Smoke Style"


def test_create_style_request_wraps_network_errors(monkeypatch):
    def fake_post(url: str, authcfg_id: str = "", data: dict | None = None) -> str:
        del url, authcfg_id, data
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(style, "post", fake_post)

    with pytest.raises(StyleAPIError, match="style create request failed"):
        style.create_style_request(
            BASE_URL,
            AUTHCFG_ID,
            CreateStyleRequest(name="Style", data={}, organization=3),
        )


def test_create_style_request_rejects_invalid_response(monkeypatch):
    def fake_post(url: str, authcfg_id: str = "", data: dict | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"name": "Style"})

    monkeypatch.setattr(style, "post", fake_post)

    with pytest.raises(StylePayloadError):
        style.create_style_request(
            BASE_URL,
            AUTHCFG_ID,
            CreateStyleRequest(name="Style", data={}, organization=3),
        )
