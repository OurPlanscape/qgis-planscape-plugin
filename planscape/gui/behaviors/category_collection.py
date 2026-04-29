from __future__ import annotations

from typing import TYPE_CHECKING, List

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import CategoryCollection, Model

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class CategoryCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> List[Model]:  # noqa: ARG002
        if not isinstance(model, CategoryCollection):
            return []
        return list(model.categories)

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> List[QAction]:  # noqa: ARG002
        return [action("New Category", context, noop), refresh_action(context, item)]
