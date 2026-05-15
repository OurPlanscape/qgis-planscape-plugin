from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.PyQt.QtCore import Qt

from planscape import auth
from planscape.api.dataset import create_dataset_request, update_dataset_request
from planscape.api.exceptions import DatasetAPIError
from planscape.gui.dataset_dialog import DatasetDialog
from planscape.models.api.dataset import CreateDatasetRequest, UpdateDatasetRequest
from planscape.models.domain.dataset import DatasetPreferredDisplayType, DatasetSelectionType
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
        preferred_display_type=DatasetPreferredDisplayType(dialog.dataset_preferred_display_type()),
        selection_type=DatasetSelectionType(dialog.dataset_selection_type()),
        organization=dialog.dataset_organization(),
        version=dialog.dataset_version(),
        modules=dialog.dataset_modules(),
    )
    try:
        created_dataset = create_dataset_request(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            request,
        )
    except DatasetAPIError:
        return

    _increment_dataset_count(item)
    context.refresh_node(item)
    _ensure_dataset_child(item, created_dataset)


def update_dataset(dataset: Dataset, context: DockContext, item: QTreeWidgetItem) -> None:
    if dataset.id is None:
        return

    dialog = DatasetDialog(
        parent=context.parent,
        dataset_id=str(dataset.id),
        name=dataset.name,
        visibility=dataset.visibility.value.lower(),
        preferred_display_type=dataset.preferred_display_type.value,
        selection_type=dataset.selection_type.value,
        modules=dataset.modules,
    )
    if not dialog.exec():
        return

    request = UpdateDatasetRequest(
        name=dialog.dataset_name(),
        visibility=WorkspaceVisibility(dialog.dataset_visibility().upper()),
        preferred_display_type=DatasetPreferredDisplayType(dialog.dataset_preferred_display_type()),
        selection_type=DatasetSelectionType(dialog.dataset_selection_type()),
        modules=dialog.dataset_modules(),
    )
    try:
        updated_dataset = update_dataset_request(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            dataset.id,
            request,
        )
    except DatasetAPIError:
        return

    item.setText(0, updated_dataset.node_label())
    item.setData(0, Qt.ItemDataRole.UserRole, updated_dataset)


def _increment_dataset_count(item: QTreeWidgetItem) -> None:
    from planscape.models.domain import DatasetCollection

    model = item.data(0, Qt.ItemDataRole.UserRole)
    if not isinstance(model, DatasetCollection) or model.count is None:
        return

    model.count += 1
    item.setText(0, model.node_label())
    item.setData(0, Qt.ItemDataRole.UserRole, model)


def _ensure_dataset_child(item: QTreeWidgetItem, dataset: Dataset) -> None:
    from planscape.gui.dock_nodes import model_item
    from planscape.models.domain import DatasetCollection

    dataset_key = dataset.node_key()
    for index in range(item.childCount()):
        child_model = item.child(index).data(0, Qt.ItemDataRole.UserRole)
        if getattr(child_model, "node_key", lambda: None)() == dataset_key:
            return

    collection = item.data(0, Qt.ItemDataRole.UserRole)
    if isinstance(collection, DatasetCollection):
        collection.datasets.append(dataset)
        item.setData(0, Qt.ItemDataRole.UserRole, collection)

    item.addChild(model_item(dataset))
