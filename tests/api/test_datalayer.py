import json

import pytest

from planscape.api import datalayer
from planscape.api.exceptions import DataLayerAPIError, DataLayerPayloadError
from planscape.models.api.datalayer import CreateDataLayerRequest
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException

BASE_URL = "https://dev.planscape.org/planscape-backend"
AUTHCFG_ID = "authcfg-id"


def test_retrieve_datalayer_urls_request_calls_fetch_with_datalayer_url(monkeypatch):
    captured = {}

    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        return json.dumps({"layer_url": "https://example.test/tiles/dynamic/{z}/{x}/{y}?layer=10"})

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    response = datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)

    assert captured == {"url": f"{BASE_URL}/v2/datalayers/10/urls/", "authcfg_id": AUTHCFG_ID}
    assert response.layer_url == "https://example.test/tiles/dynamic/{z}/{x}/{y}?layer=10"


def test_retrieve_datalayer_urls_request_logs_api_call(monkeypatch):
    logs = []

    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps({"layer_url": "https://example.test/layer"})

    monkeypatch.setattr(datalayer.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)

    assert logs == [f"[API] SUCCESS:GET:{BASE_URL}/v2/datalayers/10/urls/"]


def test_retrieve_datalayer_urls_request_logs_api_failure(monkeypatch):
    logs = []

    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(datalayer.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(DataLayerAPIError, match="failed"):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)

    assert logs == [
        f"[API] FAILED:GET:{BASE_URL}/v2/datalayers/10/urls/:Planscape datalayer URLs request failed: failed"
    ]


def test_retrieve_datalayer_urls_request_wraps_network_errors(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(DataLayerAPIError, match="datalayer URLs request failed"):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)


def test_retrieve_datalayer_urls_request_wraps_invalid_json(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return "not json"

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(DataLayerAPIError):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)


def test_retrieve_datalayer_urls_request_wraps_invalid_schema(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps({"url": "https://example.test/layer"})

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(DataLayerPayloadError):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)


def test_create_datalayer_request_posts_admin_payload(monkeypatch):
    captured = {}

    def fake_post(url: str, authcfg_id: str = "", data: dict | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps(
            {
                "datalayer": {"id": 20, "name": "Smoke", "type": "RASTER", "map_service_type": "COG"},
                "upload_to": {"url": "https://storage.example/upload"},
            }
        )

    monkeypatch.setattr(datalayer, "post", fake_post)

    response = datalayer.create_datalayer_request(
        BASE_URL,
        AUTHCFG_ID,
        CreateDataLayerRequest(
            name="Smoke",
            dataset=10,
            organization=3,
            category=4,
            layer_info={"crs": "EPSG:3857"},
            original_name="smoke.tif",
        ),
    )

    assert captured["url"] == f"{BASE_URL}/v2/admin/datalayers/"
    assert captured["authcfg_id"] == AUTHCFG_ID
    assert captured["data"]["name"] == "Smoke"
    assert captured["data"]["dataset"] == 10
    assert captured["data"]["organization"] == 3
    assert captured["data"]["category"] == 4
    assert captured["data"]["type"] == "RASTER"
    assert captured["data"]["geometry_type"] == "RASTER"
    assert captured["data"]["map_service_type"] == "COG"
    assert response.datalayer.id == 20
    assert response.upload_to.url == "https://storage.example/upload"


def test_update_datalayer_status_request_posts_admin_payload(monkeypatch):
    captured = {}

    def fake_post(url: str, authcfg_id: str = "", data: dict | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps({"id": 20, "status": "READY"})

    monkeypatch.setattr(datalayer, "post", fake_post)

    response = datalayer.update_datalayer_status_request(BASE_URL, AUTHCFG_ID, 20, 3, "READY")

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/datalayers/20/change_status/",
        "authcfg_id": AUTHCFG_ID,
        "data": {"organization": 3, "status": "READY"},
    }
    assert response == {"id": 20, "status": "READY"}
