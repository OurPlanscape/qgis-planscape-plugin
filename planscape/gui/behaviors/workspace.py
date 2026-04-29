from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import DatasetCollection, Model, StyleCollection, UserCollection, Workspace

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class WorkspaceBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> list[Model]:  # noqa: ARG002
        if not isinstance(model, Workspace):
            return []
        return [
            DatasetCollection(workspace_id=model.id, datasets=list(model.datasets)),
            StyleCollection(workspace_id=model.id, styles=list(model.styles)),
            UserCollection(workspace_id=model.id, users=list(model.users)),
        ]

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [action("Edit", context, noop), refresh_action(context, item)]
