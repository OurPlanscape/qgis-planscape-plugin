from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import DatasetCollection, Model

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class DatasetCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> list[Model]:  # noqa: ARG002
        if not isinstance(model, DatasetCollection):
            return []
        return list(model.datasets)

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [action("New Dataset", context, noop), refresh_action(context, item)]
