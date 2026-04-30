from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.PyQt.QtWidgets import QAction

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, refresh_action
from planscape.gui.commands.workspace import update_workspace
from planscape.models.domain import DatasetCollection, Model, StyleCollection, UserCollection, Workspace

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QTreeWidgetItem


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

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:
        if not isinstance(model, Workspace):
            return []

        edit_action = QAction("Edit", context.tree)
        edit_action.triggered.connect(lambda: update_workspace(model, context, item))
        return [edit_action, refresh_action(context, item)]
