import json

import pytest

from planscape.api import dataset
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException

BASE_URL = "https://dev.planscape.org/planscape-backend"
AUTHCFG_ID = "authcfg-id"


def test_browse_dataset_request_calls_fetch_with_dataset_url(monkeypatch):
    captured = {}

    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        return json.dumps([{"id": 1531, "name": "Layer", "path": ["Category"], "type": "RASTER"}])

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    tree = dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)

    assert captured == {"url": f"{BASE_URL}/v2/datasets/3/browse/", "authcfg_id": AUTHCFG_ID}
    assert tree.categories[0].name == "Category"
    assert tree.categories[0].datalayers[0].name == "Layer"


def test_browse_dataset_request_logs_api_call(monkeypatch):
    logs = []

    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps([])

    monkeypatch.setattr(dataset.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)

    assert logs == [f"[API] GET:{BASE_URL}/v2/datasets/3/browse/"]


def test_browse_dataset_request_rejects_paginated_response(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps({"count": 0, "results": []})

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(dataset.DatasetApiError, match="invalid dataset browse response"):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)


def test_browse_dataset_request_wraps_network_errors(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(dataset.DatasetApiError, match="dataset browse request failed"):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)


def test_browse_dataset_request_wraps_invalid_json(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return "not json"

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(dataset.DatasetApiError, match="invalid JSON"):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)


def test_browse_dataset_request_wraps_invalid_schema(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps([{"id": 1531, "path": ["Category"], "type": "RASTER"}])

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(dataset.DatasetApiError, match="invalid dataset browse response"):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)
