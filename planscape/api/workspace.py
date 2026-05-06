from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from planscape.models.api.workspace import (
    CreateWorkspaceRequest,
    PaginatedWorkspaceResponse,
    UpdateWorkspaceRequest,
    WorkspaceDatasetListResponse,
    WorkspacePayloadError,
    WorkspaceResponse,
    WorkspaceStyleListResponse,
    WorkspaceUserAccessListResponse,
)
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import fetch, post
from planscape.tools.network import put

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.domain.dataset import Dataset
    from planscape.models.domain.style import Style
    from planscape.models.domain.user import User
    from planscape.models.domain.workspace import Workspace

WORKSPACES_PATH = "/v2/admin/workspaces/"
logger = logging.getLogger(__name__)


class WorkspaceApiError(Exception):
    pass


def list_workspaces_request(
    base_url: str,
    authcfg_id: str,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Workspace]:
    params = _pagination_params(limit, offset)
    url = _workspaces_url(base_url)
    logger.info("[API] GET:%s", url)
    response = _request_json(
        lambda: fetch(url, authcfg_id=authcfg_id, params=params),
        "Planscape workspace list request failed",
    )

    try:
        if isinstance(response, list):
            return [_workspace_from_response(item) for item in response]
        if not isinstance(response, dict):
            message = "Planscape returned an invalid workspace list response."
            raise WorkspaceApiError(message)
        return PaginatedWorkspaceResponse.from_dict(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace list response."
        raise WorkspaceApiError(message) from exc


def create_workspace_request(base_url: str, authcfg_id: str, request: CreateWorkspaceRequest) -> Workspace:
    url = _workspaces_url(base_url)
    logger.info("[API] POST:%s", url)
    response = _request_json(
        lambda: post(url, authcfg_id=authcfg_id, data=request.to_dict()),
        "Planscape workspace create request failed",
    )
    if not isinstance(response, dict):
        message = "Planscape returned an invalid workspace response."
        raise WorkspaceApiError(message)
    return _workspace_from_response(response)


def update_workspace_request(
    base_url: str,
    authcfg_id: str,
    workspace_id: int | str,
    request: UpdateWorkspaceRequest,
) -> Workspace:
    url = _workspace_url(base_url, workspace_id)
    logger.info("[API] PUT:%s", url)
    response = _request_json(
        lambda: put(url, authcfg_id=authcfg_id, data=request.to_dict()),
        "Planscape workspace update request failed",
    )
    if not isinstance(response, dict):
        message = "Planscape returned an invalid workspace response."
        raise WorkspaceApiError(message)
    return _workspace_from_response(response)


def list_workspace_datasets_request(base_url: str, authcfg_id: str, workspace_id: int | str) -> list[Dataset]:
    url = _workspace_child_url(base_url, workspace_id, "datasets")
    logger.info("[API] GET:%s", url)
    response = _request_json_list(
        lambda: fetch(url, authcfg_id=authcfg_id),
        "Planscape workspace dataset list request failed",
    )

    try:
        return WorkspaceDatasetListResponse.from_list(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace dataset list response."
        raise WorkspaceApiError(message) from exc


def list_workspace_styles_request(base_url: str, authcfg_id: str, workspace_id: int | str) -> list[Style]:
    url = _workspace_child_url(base_url, workspace_id, "styles")
    logger.info("[API] GET:%s", url)
    response = _request_json_list(
        lambda: fetch(url, authcfg_id=authcfg_id),
        "Planscape workspace style list request failed",
    )

    try:
        return WorkspaceStyleListResponse.from_list(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace style list response."
        raise WorkspaceApiError(message) from exc


def list_workspace_users_request(base_url: str, authcfg_id: str, workspace_id: int | str) -> list[User]:
    url = _workspace_child_url(base_url, workspace_id, "users")
    logger.info("[API] GET:%s", url)
    response = _request_json_list(
        lambda: fetch(url, authcfg_id=authcfg_id),
        "Planscape workspace user list request failed",
    )

    try:
        return WorkspaceUserAccessListResponse.from_list(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace user list response."
        raise WorkspaceApiError(message) from exc


def _workspace_from_response(response: object) -> Workspace:
    if not isinstance(response, dict):
        message = "Planscape returned an invalid workspace response."
        raise WorkspaceApiError(message)
    try:
        return WorkspaceResponse.from_dict(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace response."
        raise WorkspaceApiError(message) from exc


def _request_json(request: Callable[[], str], failure_message: str) -> dict[str, Any] | list[Any]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise WorkspaceApiError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON workspace response."
        raise WorkspaceApiError(message) from exc

    return body


def _request_json_list(request: Callable[[], str], failure_message: str) -> list[object]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise WorkspaceApiError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON workspace response."
        raise WorkspaceApiError(message) from exc

    if not isinstance(body, list):
        message = "Planscape returned an invalid workspace list response."
        raise WorkspaceApiError(message)
    return body


def _pagination_params(limit: int | None, offset: int | None) -> dict[str, str] | None:
    params = {}
    if limit is not None:
        params["limit"] = str(limit)
    if offset is not None:
        params["offset"] = str(offset)
    return params or None


def _workspaces_url(base_url: str) -> str:
    return f"{base_url}{WORKSPACES_PATH}"


def _workspace_url(base_url: str, workspace_id: int | str) -> str:
    return f"{_workspaces_url(base_url)}{workspace_id}/"


def _workspace_child_url(base_url: str, workspace_id: int | str, child: str) -> str:
    return f"{_workspace_url(base_url, workspace_id)}{child}/"
