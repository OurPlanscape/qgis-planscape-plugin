from __future__ import annotations

from typing import TYPE_CHECKING, List

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import Model, StyleCollection

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class StyleCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> List[Model]:  # noqa: ARG002
        if not isinstance(model, StyleCollection):
            return []
        return list(model.styles)

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> List[QAction]:  # noqa: ARG002
        return [action("New Style", context, noop), refresh_action(context, item)]
