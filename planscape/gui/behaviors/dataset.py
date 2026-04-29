from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import CategoryCollection, DataLayerCollection, Dataset, Model

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class DatasetBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> list[Model]:  # noqa: ARG002
        if not isinstance(model, Dataset):
            return []
        return [
            DataLayerCollection(dataset_id=model.id, datalayers=list(model.datalayers)),
            CategoryCollection(dataset_id=model.id, categories=list(model.categories)),
        ]

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [action("Edit", context, noop), refresh_action(context, item)]
