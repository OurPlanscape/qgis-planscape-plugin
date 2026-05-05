import json

import pytest

from planscape.api import datalayer
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

    assert logs == [f"[API] GET:{BASE_URL}/v2/datalayers/10/urls/"]


def test_retrieve_datalayer_urls_request_wraps_network_errors(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(datalayer.DataLayerApiError, match="datalayer URLs request failed"):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)


def test_retrieve_datalayer_urls_request_wraps_invalid_json(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return "not json"

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(datalayer.DataLayerApiError, match="invalid JSON"):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)


def test_retrieve_datalayer_urls_request_wraps_invalid_schema(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps({"url": "https://example.test/layer"})

    monkeypatch.setattr(datalayer, "fetch", fake_fetch)

    with pytest.raises(datalayer.DataLayerApiError, match="invalid datalayer URLs response"):
        datalayer.retrieve_datalayer_urls_request(BASE_URL, AUTHCFG_ID, 10)
