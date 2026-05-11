from __future__ import annotations

from typing import TYPE_CHECKING

from planscape.gui.behaviors.base import DockContext, DockNodeBehavior
from planscape.models.domain import Model, ModuleCollection

if TYPE_CHECKING:
    from collections.abc import Sequence


class ModuleCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> Sequence[Model]:  # noqa: ARG002
        if not isinstance(model, ModuleCollection):
            return []
        return list(model.modules)
