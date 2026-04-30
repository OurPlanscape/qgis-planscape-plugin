from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, refresh_action
from planscape.gui.commands.workspace import create_workspace
from planscape.models.domain import Model, Server

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class ServerBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> list[Model]:  # noqa: ARG002
        if not isinstance(model, Server):
            return []
        return list(model.workspaces)

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [
            action("Create new Workspace", context, lambda: create_workspace(context, item)),
            refresh_action(context, item),
            action("Login another env", context, context.login_another_env),
            action("Logout", context, context.logout),
        ]
