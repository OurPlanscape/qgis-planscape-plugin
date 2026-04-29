from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from planscape.models.api.workspace import (
    CreateWorkspaceRequest,
    PaginatedWorkspaceResponse,
    UpdateWorkspaceRequest,
    WorkspacePayloadError,
    WorkspaceResponse,
)
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import fetch, post
from planscape.tools.network import put

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.domain.workspace import Workspace

WORKSPACES_PATH = "/v2/admin/workspaces/"
logger = logging.getLogger(__name__)


class WorkspaceServiceError(Exception):
    pass


def list_workspaces(
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
        return PaginatedWorkspaceResponse.from_dict(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace list response."
        raise WorkspaceServiceError(message) from exc


def create_workspace(base_url: str, authcfg_id: str, request: CreateWorkspaceRequest) -> Workspace:
    url = _workspaces_url(base_url)
    logger.info("[API] POST:%s", url)
    response = _request_json(
        lambda: post(url, authcfg_id=authcfg_id, data=request.to_dict()),
        "Planscape workspace create request failed",
    )
    return _workspace_from_response(response)


def update_workspace(
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
    return _workspace_from_response(response)


def _workspace_from_response(response: dict[str, object]) -> Workspace:
    try:
        return WorkspaceResponse.from_dict(response).to_domain()
    except WorkspacePayloadError as exc:
        message = "Planscape returned an invalid workspace response."
        raise WorkspaceServiceError(message) from exc


def _request_json(request: Callable[[], str], failure_message: str) -> dict[str, object]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise WorkspaceServiceError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON workspace response."
        raise WorkspaceServiceError(message) from exc

    if not isinstance(body, dict):
        message = "Planscape returned an invalid workspace response."
        raise WorkspaceServiceError(message)
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
