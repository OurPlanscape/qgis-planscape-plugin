from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.PyQt.QtCore import Qt

from planscape import auth
from planscape.gui.workspace_dialog import WorkspaceDialog
from planscape.models.api.workspace import CreateWorkspaceRequest, UpdateWorkspaceRequest
from planscape.models.domain.workspace import WorkspaceVisibility
from planscape.services.workspace_service import (
    WorkspaceServiceError,
    update_workspace,
)
from planscape.services.workspace_service import (
    create_workspace as create_workspace_request,
)

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QTreeWidgetItem

    from planscape.gui.behaviors import DockContext
    from planscape.models.domain import Workspace


def create_workspace(context: DockContext, item: QTreeWidgetItem) -> None:
    dialog = WorkspaceDialog(parent=context.parent)
    if not dialog.exec():
        return

    request = CreateWorkspaceRequest(
        name=dialog.workspace_name(),
        visibility=WorkspaceVisibility(dialog.workspace_visibility().upper()),
    )
    try:
        create_workspace_request(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            request,
        )
    except WorkspaceServiceError:
        return

    context.refresh_node(item)


def edit_workspace(workspace: Workspace, context: DockContext, item: QTreeWidgetItem) -> None:
    if workspace.id is None:
        return

    dialog = WorkspaceDialog(
        parent=context.parent,
        workspace_id=str(workspace.id),
        name=workspace.name,
        visibility=workspace.visibility.value.lower(),
    )
    if not dialog.exec():
        return

    request = UpdateWorkspaceRequest(
        name=dialog.workspace_name(),
        visibility=WorkspaceVisibility(dialog.workspace_visibility().upper()),
    )
    try:
        updated_workspace = update_workspace(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            workspace.id,
            request,
        )
    except WorkspaceServiceError:
        return

    item.setText(0, updated_workspace.node_label())
    item.setData(0, Qt.ItemDataRole.UserRole, updated_workspace)
