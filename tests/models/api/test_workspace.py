import pytest

from planscape.models.api.workspace import (
    CreateWorkspaceRequest,
    PaginatedWorkspaceResponse,
    UpdateWorkspaceRequest,
    WorkspacePayloadError,
    WorkspaceResponse,
)
from planscape.models.domain import Workspace, WorkspaceVisibility


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
