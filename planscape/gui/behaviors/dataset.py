from __future__ import annotations

from typing import TYPE_CHECKING

from planscape import auth
from planscape.api.dataset import DatasetApiError, browse_dataset_request
from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import DataLayerCollection, Dataset, Model

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class DatasetBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> Sequence[Model]:  # noqa: ARG002
        if not isinstance(model, Dataset):
            return []
        if model.id is None:
            return [DataLayerCollection(dataset_id=model.id)]
        try:
            browse_tree = browse_dataset_request(
                auth.get_base_url(auth.get_environment()),
                auth.ensure_authenticated(),
                model.id,
            )
        except DatasetApiError:
            return [DataLayerCollection(dataset_id=model.id)]

        return [
            DataLayerCollection(
                dataset_id=model.id,
                categories=browse_tree.categories,
                datalayers=browse_tree.datalayers,
            )
        ]

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [action("Edit", context, noop), refresh_action(context, item)]
