from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsRasterLayer
from qgis.utils import iface

from planscape.models.domain import DatasetCollection
from planscape.processing.import_raster import DATASET, DATASET_MODULES, INPUT, WORKSPACE

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QTreeWidgetItem

    from planscape.models.domain import Dataset


def open_import_raster_dialog(dataset: Dataset, item: QTreeWidgetItem) -> None:
    if dataset.id is None:
        return

    import processing

    parameters: dict[str, object] = {DATASET: int(dataset.id), DATASET_MODULES: ",".join(dataset.modules)}
    workspace_id = _workspace_id(item)
    if workspace_id is not None:
        parameters[WORKSPACE] = int(workspace_id)

    active_layer = iface.activeLayer()
    if isinstance(active_layer, QgsRasterLayer):
        parameters[INPUT] = active_layer

    processing.execAlgorithmDialog("planscape:import_raster", parameters)


def _workspace_id(item: QTreeWidgetItem) -> int | str | None:
    from planscape.gui.dock_nodes import item_node

    current = item.parent()
    while current is not None:
        node = item_node(current)
        if isinstance(node, DatasetCollection):
            return node.workspace_id
        current = current.parent()
    return None
