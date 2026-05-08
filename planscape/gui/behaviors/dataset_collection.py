from __future__ import annotations

from typing import TYPE_CHECKING

from planscape import auth
from planscape.api.exceptions import WorkspaceAPIError
from planscape.api.workspace import list_workspace_datasets_request
from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, refresh_action
from planscape.gui.commands.dataset import create_dataset
from planscape.models.domain import DatasetCollection, Model

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class DatasetCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> Sequence[Model]:  # noqa: ARG002
        if not isinstance(model, DatasetCollection):
            return []
        if model.workspace_id is None:
            return []
        try:
            return list_workspace_datasets_request(
                auth.get_base_url(auth.get_environment()),
                auth.ensure_authenticated(),
                model.workspace_id,
            )
        except WorkspaceAPIError:
            return []

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:
        if not isinstance(model, DatasetCollection) or model.workspace_id is None:
            return [refresh_action(context, item)]
        return [
            action("New Dataset", context, lambda: create_dataset(context, item, model.workspace_id)),  # type: ignore
            refresh_action(context, item),
        ]
