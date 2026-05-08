import pytest

from planscape.api.exceptions import WorkspacePayloadError
from planscape.models.api.workspace import (
    CreateWorkspaceRequest,
    PaginatedWorkspaceResponse,
    UpdateWorkspaceRequest,
    WorkspaceDatasetListResponse,
    WorkspaceResponse,
    WorkspaceStyleListResponse,
    WorkspaceUserAccessListResponse,
)
from planscape.models.domain import Dataset, Style, User, Workspace, WorkspaceVisibility


def test_create_workspace_request_serializes_payload():
    request = CreateWorkspaceRequest(name="Regional Plan", visibility=WorkspaceVisibility.PUBLIC)

    assert request.to_dict() == {"name": "Regional Plan", "visibility": "PUBLIC"}


def test_create_workspace_request_defaults_to_private_visibility():
    request = CreateWorkspaceRequest(name="Regional Plan")

    assert request.to_dict() == {"name": "Regional Plan", "visibility": "PRIVATE"}


def test_update_workspace_request_omits_none_fields():
    request = UpdateWorkspaceRequest(visibility=WorkspaceVisibility.PUBLIC)

    assert request.to_dict() == {"visibility": "PUBLIC"}


def test_workspace_response_parses_full_workspace_payload():
    response = WorkspaceResponse.from_dict(
        {
            "id": 10,
            "name": "Regional Plan",
            "visibility": "PUBLIC",
            "created_at": None,
            "updated_at": "2026-04-29T12:00:00Z",
            "deleted_at": None,
        }
    )

    assert response.id == 10
    assert response.name == "Regional Plan"
    assert response.visibility == WorkspaceVisibility.PUBLIC
    assert response.updated_at == "2026-04-29T12:00:00Z"


def test_workspace_response_accepts_create_response_shape():
    response = WorkspaceResponse.from_dict({"name": "Regional Plan", "visibility": "PRIVATE"})

    assert response.to_domain() == Workspace(id=None, name="Regional Plan")


def test_workspace_response_maps_to_domain_workspace():
    response = WorkspaceResponse.from_dict({"id": 10, "name": "Regional Plan", "visibility": "PUBLIC"})

    workspace = response.to_domain()

    assert workspace.id == 10
    assert workspace.name == "Regional Plan"
    assert workspace.visibility == WorkspaceVisibility.PUBLIC


def test_paginated_workspace_response_parses_results():
    response = PaginatedWorkspaceResponse.from_dict(
        {
            "count": 2,
            "next": "https://example.test/workspaces/?offset=2",
            "previous": None,
            "results": [
                {"id": 10, "name": "First", "visibility": "PRIVATE"},
                {"id": 11, "name": "Second", "visibility": "PUBLIC"},
            ],
        }
    )

    assert response.count == 2
    assert response.next == "https://example.test/workspaces/?offset=2"
    assert [workspace.name for workspace in response.to_domain()] == ["First", "Second"]


def test_workspace_response_rejects_invalid_visibility():
    with pytest.raises(WorkspacePayloadError, match="Unsupported workspace visibility"):
        WorkspaceResponse.from_dict({"name": "Regional Plan", "visibility": "SHARED"})


def test_paginated_workspace_response_rejects_invalid_results_shape():
    with pytest.raises(WorkspacePayloadError, match="results must be a list"):
        PaginatedWorkspaceResponse.from_dict({"count": 1, "results": {}})


def test_workspace_dataset_list_response_parses_raw_list():
    response = WorkspaceDatasetListResponse.from_list([{"id": 20, "name": "Base Data", "visibility": "PUBLIC"}])

    assert response.to_domain() == [Dataset(id=20, name="Base Data", visibility=WorkspaceVisibility.PUBLIC)]


def test_workspace_style_list_response_parses_raw_list():
    response = WorkspaceStyleListResponse.from_list([{"id": 30, "name": "Default", "type": "VECTOR"}])

    assert response.to_domain() == [Style(id=30, name="Default")]


def test_workspace_user_access_list_response_parses_raw_list():
    response = WorkspaceUserAccessListResponse.from_list(
        [
            {
                "user_id": 40,
                "email": "planner@example.test",
                "first_name": "Regional",
                "last_name": "Planner",
                "role": "OWNER",
            }
        ]
    )

    assert response.to_domain() == [User(id=40, name="Regional Planner", email="planner@example.test")]


def test_workspace_child_list_response_rejects_paginated_shape():
    with pytest.raises(WorkspacePayloadError, match="must be a list"):
        WorkspaceDatasetListResponse.from_list({"count": 1, "results": []})  # type: ignore[arg-type]


def test_workspace_child_list_response_rejects_missing_required_fields():
    with pytest.raises(WorkspacePayloadError, match="name must be a string"):
        WorkspaceStyleListResponse.from_list([{"id": 30}])
