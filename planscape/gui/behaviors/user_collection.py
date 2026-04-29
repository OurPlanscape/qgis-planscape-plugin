from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import Model, UserCollection

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class UserCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> list[Model]:  # noqa: ARG002
        if not isinstance(model, UserCollection):
            return []
        return list(model.users)

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [action("Invite User", context, noop), refresh_action(context, item)]
