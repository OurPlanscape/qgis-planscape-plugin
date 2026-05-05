from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior
from planscape.models.domain import Category, Model

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class CategoryBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> Sequence[Model]:  # noqa: ARG002
        if not isinstance(model, Category):
            return []
        return [*model.categories, *model.datalayers]

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return []
