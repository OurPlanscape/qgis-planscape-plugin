from __future__ import annotations

import json
from typing import TYPE_CHECKING

from qgis.core import QgsRasterLayer
from qgis.utils import iface

from planscape.processing.import_raster import DATASET, INPUT, METADATA
from planscape.processing.raster_import import module_metadata

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QTreeWidgetItem

    from planscape.models.domain import Dataset


def open_import_raster_dialog(dataset: Dataset, item: QTreeWidgetItem) -> None:
    del item
    if dataset.id is None:
        return

    import processing

    parameters: dict[str, object] = {
        DATASET: int(dataset.id),
        METADATA: json.dumps({"modules": module_metadata(dataset.modules)}, indent=2),
    }
    active_layer = iface.activeLayer()
    if isinstance(active_layer, QgsRasterLayer):
        parameters[INPUT] = active_layer

    processing.execAlgorithmDialog("planscape:import_raster", parameters)
