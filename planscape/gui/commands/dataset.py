from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.PyQt.QtCore import Qt

from planscape import auth
from planscape.api.dataset import create_dataset_request, update_dataset_request
from planscape.api.exceptions import DatasetApiError
from planscape.gui.dataset_dialog import DatasetDialog
from planscape.models.api.dataset import CreateDatasetRequest, UpdateDatasetRequest
from planscape.models.domain.workspace import WorkspaceVisibility

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QTreeWidgetItem

    from planscape.gui.behaviors import DockContext
    from planscape.models.domain import Dataset


def create_dataset(context: DockContext, item: QTreeWidgetItem, workspace_id: int | str) -> None:
    dialog = DatasetDialog(parent=context.parent)
    if not dialog.exec():
        return

    request = CreateDatasetRequest(
        workspace_id=workspace_id,
        name=dialog.dataset_name(),
        visibility=WorkspaceVisibility(dialog.dataset_visibility().upper()),
        organization=dialog.dataset_organization(),
        version=dialog.dataset_version(),
        modules=dialog.dataset_modules(),
    )
    try:
        create_dataset_request(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            request,
        )
    except DatasetApiError:
        return

    context.refresh_node(item)


def update_dataset(dataset: Dataset, context: DockContext, item: QTreeWidgetItem) -> None:
    if dataset.id is None:
        return

    dialog = DatasetDialog(
        parent=context.parent,
        dataset_id=str(dataset.id),
        name=dataset.name,
        visibility=dataset.visibility.value.lower(),
    )
    if not dialog.exec():
        return

    request = UpdateDatasetRequest(
        name=dialog.dataset_name(),
        visibility=WorkspaceVisibility(dialog.dataset_visibility().upper()),
    )
    try:
        updated_dataset = update_dataset_request(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            dataset.id,
            request,
        )
    except DatasetApiError:
        return

    item.setText(0, updated_dataset.node_label())
    item.setData(0, Qt.ItemDataRole.UserRole, updated_dataset)
