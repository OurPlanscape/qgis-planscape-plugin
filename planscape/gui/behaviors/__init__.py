from __future__ import annotations

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior
from planscape.gui.behaviors.category_collection import CategoryCollectionBehavior
from planscape.gui.behaviors.datalayer_collection import DataLayerCollectionBehavior
from planscape.gui.behaviors.dataset import DatasetBehavior
from planscape.gui.behaviors.dataset_collection import DatasetCollectionBehavior
from planscape.gui.behaviors.server import ServerBehavior
from planscape.gui.behaviors.style_collection import StyleCollectionBehavior
from planscape.gui.behaviors.user_collection import UserCollectionBehavior
from planscape.gui.behaviors.workspace import WorkspaceBehavior
from planscape.models.domain import Model, NodeKind

NODE_BEHAVIORS: dict[NodeKind, DockNodeBehavior] = {
    NodeKind.SERVER: ServerBehavior(),
    NodeKind.WORKSPACE: WorkspaceBehavior(),
    NodeKind.DATASET_COLLECTION: DatasetCollectionBehavior(),
    NodeKind.STYLE_COLLECTION: StyleCollectionBehavior(),
    NodeKind.USER_COLLECTION: UserCollectionBehavior(),
    NodeKind.DATASET: DatasetBehavior(),
    NodeKind.DATALAYER_COLLECTION: DataLayerCollectionBehavior(),
    NodeKind.CATEGORY_COLLECTION: CategoryCollectionBehavior(),
}


def behavior_for(model: Model) -> DockNodeBehavior:
    return NODE_BEHAVIORS.get(model.kind, DockNodeBehavior())


__all__ = ["DockContext", "DockNodeBehavior", "behavior_for"]
