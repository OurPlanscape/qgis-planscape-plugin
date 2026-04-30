import json

import pytest

from planscape.api import workspace
from planscape.models.api.workspace import CreateWorkspaceRequest, UpdateWorkspaceRequest
from planscape.models.domain import WorkspaceVisibility
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException

BASE_URL = "https://dev.planscape.org/planscape-backend"
AUTHCFG_ID = "authcfg-id"


def test_list_workspaces_request_calls_fetch_with_pagination(monkeypatch):
    captured = {}

    def fake_fetch(url: str, authcfg_id: str = "", params: dict[str, str] | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["params"] = params
        return json.dumps(
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [{"id": 10, "name": "Regional Plan", "visibility": "PUBLIC"}],
            }
        )

    monkeypatch.setattr(workspace, "fetch", fake_fetch)

    workspaces = workspace.list_workspaces_request(BASE_URL, AUTHCFG_ID, limit=25, offset=50)

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/workspaces/",
        "authcfg_id": AUTHCFG_ID,
        "params": {"limit": "25", "offset": "50"},
    }
    assert len(workspaces) == 1
    assert workspaces[0].id == 10
    assert workspaces[0].visibility == WorkspaceVisibility.PUBLIC


def test_list_workspaces_request_logs_api_call(monkeypatch):
    logs = []

    def fake_fetch(url: str, authcfg_id: str = "", params: dict[str, str] | None = None) -> str:
        del url, authcfg_id, params
        return json.dumps({"count": 0, "next": None, "previous": None, "results": []})

    monkeypatch.setattr(workspace.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(workspace, "fetch", fake_fetch)

    workspace.list_workspaces_request(BASE_URL, AUTHCFG_ID)

    assert logs == [f"[API] GET:{BASE_URL}/v2/admin/workspaces/"]


def test_list_workspaces_request_omits_empty_pagination_params(monkeypatch):
    captured = {}

    def fake_fetch(url: str, authcfg_id: str = "", params: dict[str, str] | None = None) -> str:
        del url, authcfg_id
        captured["params"] = params
        return json.dumps({"count": 0, "next": None, "previous": None, "results": []})

    monkeypatch.setattr(workspace, "fetch", fake_fetch)

    assert workspace.list_workspaces_request(BASE_URL, AUTHCFG_ID) == []
    assert captured["params"] is None


def test_create_workspace_request_calls_post_with_request_payload(monkeypatch):
    captured = {}

    def fake_post(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps({"id": 10, "name": "Regional Plan", "visibility": "PRIVATE"})

    monkeypatch.setattr(workspace, "post", fake_post)

    created_workspace = workspace.create_workspace_request(
        BASE_URL,
        AUTHCFG_ID,
        CreateWorkspaceRequest(name="Regional Plan"),
    )

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/workspaces/",
        "authcfg_id": AUTHCFG_ID,
        "data": {"name": "Regional Plan", "visibility": "PRIVATE"},
    }
    assert created_workspace.id == 10
    assert created_workspace.name == "Regional Plan"


def test_create_workspace_request_logs_api_call(monkeypatch):
    logs = []

    def fake_post(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"name": "Regional Plan", "visibility": "PRIVATE"})

    monkeypatch.setattr(workspace.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(workspace, "post", fake_post)

    workspace.create_workspace_request(BASE_URL, AUTHCFG_ID, CreateWorkspaceRequest(name="Regional Plan"))

    assert logs == [f"[API] POST:{BASE_URL}/v2/admin/workspaces/"]


def test_update_workspace_request_calls_put_with_request_payload(monkeypatch):
    captured = {}

    def fake_put(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        captured["url"] = url
        captured["authcfg_id"] = authcfg_id
        captured["data"] = data
        return json.dumps({"id": 10, "name": "Updated Plan", "visibility": "PUBLIC"})

    monkeypatch.setattr(workspace, "put", fake_put)

    updated_workspace = workspace.update_workspace_request(
        BASE_URL,
        AUTHCFG_ID,
        10,
        UpdateWorkspaceRequest(name="Updated Plan", visibility=WorkspaceVisibility.PUBLIC),
    )

    assert captured == {
        "url": f"{BASE_URL}/v2/admin/workspaces/10/",
        "authcfg_id": AUTHCFG_ID,
        "data": {"name": "Updated Plan", "visibility": "PUBLIC"},
    }
    assert updated_workspace.id == 10
    assert updated_workspace.name == "Updated Plan"
    assert updated_workspace.visibility == WorkspaceVisibility.PUBLIC


def test_update_workspace_request_logs_api_call(monkeypatch):
    logs = []

    def fake_put(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"id": 10, "name": "Updated", "visibility": "PUBLIC"})

    monkeypatch.setattr(workspace.logger, "info", lambda message, url: logs.append(message % url))
    monkeypatch.setattr(workspace, "put", fake_put)

    workspace.update_workspace_request(BASE_URL, AUTHCFG_ID, 10, UpdateWorkspaceRequest(name="Updated"))

    assert logs == [f"[API] PUT:{BASE_URL}/v2/admin/workspaces/10/"]


def test_workspace_api_wraps_network_errors(monkeypatch):
    def fake_fetch(url: str, authcfg_id: str = "", params: dict[str, str] | None = None) -> str:
        del url, authcfg_id, params
        message = "failed"
        raise QgsPluginException(message)

    monkeypatch.setattr(workspace, "fetch", fake_fetch)

    with pytest.raises(workspace.WorkspaceApiError, match="workspace list request failed"):
        workspace.list_workspaces_request(BASE_URL, AUTHCFG_ID)


def test_workspace_api_wraps_invalid_json(monkeypatch):
    def fake_post(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        del url, authcfg_id, data
        return "not json"

    monkeypatch.setattr(workspace, "post", fake_post)

    with pytest.raises(workspace.WorkspaceApiError, match="invalid JSON"):
        workspace.create_workspace_request(BASE_URL, AUTHCFG_ID, CreateWorkspaceRequest(name="Regional Plan"))


def test_workspace_api_wraps_invalid_schema(monkeypatch):
    def fake_put(url: str, authcfg_id: str = "", data: dict[str, str] | None = None) -> str:
        del url, authcfg_id, data
        return json.dumps({"visibility": "PUBLIC"})

    monkeypatch.setattr(workspace, "put", fake_put)

    with pytest.raises(workspace.WorkspaceApiError, match="invalid workspace response"):
        workspace.update_workspace_request(BASE_URL, AUTHCFG_ID, 10, UpdateWorkspaceRequest(name="Updated"))
