from __future__ import annotations

from typing import TYPE_CHECKING

from planscape import auth
from planscape.api.dataset import browse_dataset_request
from planscape.api.exceptions import DatasetAPIError
from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, refresh_action
from planscape.gui.commands.datalayer_import import open_import_raster_dialog
from planscape.gui.commands.dataset import update_dataset
from planscape.models.domain import DataLayerCollection, Dataset, Model, Module, ModuleCollection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class DatasetBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> Sequence[Model]:  # noqa: ARG002
        if not isinstance(model, Dataset):
            return []
        if model.id is None:
            return [_module_collection(model), DataLayerCollection(dataset_id=model.id)]
        try:
            browse_tree = browse_dataset_request(
                auth.get_base_url(auth.get_environment()),
                auth.ensure_authenticated(),
                model.id,
            )
        except DatasetAPIError:
            return [_module_collection(model), DataLayerCollection(dataset_id=model.id)]

        return [
            _module_collection(model),
            DataLayerCollection(
                dataset_id=model.id,
                categories=browse_tree.categories,
                datalayers=browse_tree.datalayers,
            ),
        ]

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:
        if not isinstance(model, Dataset):
            return []
        return [
            action("Edit", context, lambda: update_dataset(model, context, item)),
            action("Import Raster...", context, lambda: open_import_raster_dialog(model, item)),
            refresh_action(context, item),
        ]

    def double_clicked(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> None:
        if not isinstance(model, Dataset):
            return
        update_dataset(model, context, item)


def _module_collection(dataset: Dataset) -> ModuleCollection:
    return ModuleCollection(
        dataset_id=dataset.id,
        modules=[Module(name=module) for module in dataset.modules],
    )
