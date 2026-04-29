from __future__ import annotations

from typing import TYPE_CHECKING, List

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, refresh_action
from planscape.models.domain import Model, Server

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class ServerBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> List[Model]:  # noqa: ARG002
        if not isinstance(model, Server):
            return []
        return list(model.workspaces)

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> List[QAction]:  # noqa: ARG002
        return [
            action("Create new Workspace", context, context.create_workspace),
            refresh_action(context, item),
            action("Login another env", context, context.login_another_env),
            action("Logout", context, context.logout),
        ]
