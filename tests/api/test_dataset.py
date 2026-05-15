import json

import pytest

from planscape.api import dataset
from planscape.api.exceptions import DatasetAPIError, DatasetPayloadError
from planscape.models.api.dataset import CreateDatasetRequest, UpdateDatasetRequest
from planscape.models.domain import WorkspaceVisibility
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException

BASE_URL = "https://dev.planscape.org/planscape-backend"
AUTHCFG_ID = "authcfg-id"


def test_create_dataset_request_calls_post_with_admin_dataset_url(monkeypatch):
    captured = {}

    def fake_post(url: str, authcfg_id: str = "", data: dict[str, object] | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps({"id": 20, "name": "Base Data", "visibility": "PRIVATE"})

    monkeypatch.setattr(dataset, "post", fake_post)

    created_dataset = dataset.create_dataset_request(
        BASE_URL, AUTHCFG_ID, CreateDatasetRequest(workspace_id=7, name="Base Data")
    )

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/datasets/",
        "authcfg_id": AUTHCFG_ID,
        "data": {
            "workspace_id": 7,
            "name": "Base Data",
            "visibility": "PRIVATE",
            "preferred_display_type": "MAIN_DATALAYERS",
            "selection_type": "SINGLE",
            "modules": ["map", "forsys", "prioritize_sub_units"],
        },
    }
    assert created_dataset.id == 20
    assert created_dataset.name == "Base Data"


def test_create_dataset_request_logs_api_call(monkeypatch):
    logs = []

    def fake_post(url: str, authcfg_id: str = "", data: dict[str, object] | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"id": 20, "name": "Base Data", "visibility": "PRIVATE"})

    monkeypatch.setattr(dataset.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(dataset, "post", fake_post)

    dataset.create_dataset_request(BASE_URL, AUTHCFG_ID, CreateDatasetRequest(workspace_id=7, name="Base Data"))

    assert logs == [f"[API] SUCCESS:POST:{BASE_URL}/v2/admin/datasets/"]


def test_update_dataset_request_calls_put_with_admin_dataset_url(monkeypatch):
    captured = {}

    def fake_put(url: str, authcfg_id: str = "", data: dict[str, object] | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps({"id": 20, "name": "Updated Data", "visibility": "PUBLIC"})

    monkeypatch.setattr(dataset, "put", fake_put)

    updated_dataset = dataset.update_dataset_request(
        BASE_URL,
        AUTHCFG_ID,
        20,
        UpdateDatasetRequest(name="Updated Data", visibility=WorkspaceVisibility.PUBLIC, modules=["map"]),
    )

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/datasets/20/",
        "authcfg_id": AUTHCFG_ID,
        "data": {"name": "Updated Data", "visibility": "PUBLIC", "modules": ["map"]},
    }
    assert updated_dataset.id == 20
    assert updated_dataset.name == "Updated Data"
    assert updated_dataset.visibility == WorkspaceVisibility.PUBLIC


def test_update_dataset_request_logs_api_call(monkeypatch):
    logs = []

    def fake_put(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"id": 20, "name": "Updated Data", "visibility": "PUBLIC"})

    monkeypatch.setattr(dataset.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(dataset, "put", fake_put)

    dataset.update_dataset_request(BASE_URL, AUTHCFG_ID, 20, UpdateDatasetRequest(name="Updated Data"))

    assert logs == [f"[API] SUCCESS:PUT:{BASE_URL}/v2/admin/datasets/20/"]


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

    assert logs == [f"[API] SUCCESS:GET:{BASE_URL}/v2/datasets/3/browse/"]


def test_browse_dataset_request_logs_api_failure(monkeypatch):
    logs = []

    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(dataset.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(DatasetAPIError, match="failed"):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)

    assert logs == [
        f"[API] FAILED:GET:{BASE_URL}/v2/datasets/3/browse/:Planscape dataset browse request failed: failed"
    ]


def test_browse_dataset_request_wraps_network_errors(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(DatasetAPIError, match="dataset browse request failed"):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)


def test_browse_dataset_request_wraps_invalid_json(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return "not json"

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(DatasetPayloadError):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)


def test_browse_dataset_request_wraps_invalid_schema(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "") -> str:
        del url, authcfg_id
        return json.dumps([{"id": 1531, "path": ["Category"], "type": "RASTER"}])

    monkeypatch.setattr(dataset, "fetch", fake_fetch)

    with pytest.raises(DatasetPayloadError):
        dataset.browse_dataset_request(BASE_URL, AUTHCFG_ID, 3)


def test_dataset_admin_request_wraps_invalid_json(monkeypatch):
    def fake_post(url: str, authcfg_id: str = "", data: dict[str, object] | None = None) -> str:
        del url, authcfg_id, data
        return "not json"

    monkeypatch.setattr(dataset, "post", fake_post)

    with pytest.raises(DatasetPayloadError):
        dataset.create_dataset_request(BASE_URL, AUTHCFG_ID, CreateDatasetRequest(workspace_id=7, name="Base Data"))


def test_dataset_admin_request_wraps_invalid_schema(monkeypatch):
    def fake_put(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"visibility": "PUBLIC"})

    monkeypatch.setattr(dataset, "put", fake_put)

    with pytest.raises(DatasetPayloadError):
        dataset.update_dataset_request(BASE_URL, AUTHCFG_ID, 20, UpdateDatasetRequest(name="Updated Data"))
