from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior
from planscape.gui.commands.datalayer import add_datalayer_to_project
from planscape.models.domain import DataLayer, Model

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QTreeWidgetItem


class DataLayerBehavior(DockNodeBehavior):
    def double_clicked(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> None:  # noqa: ARG002
        if not isinstance(model, DataLayer):
            return
        if model.id is None or model.status != "READY":
            return
        add_datalayer_to_project(model)
