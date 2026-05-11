from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.module import Module


@dataclass
class ModuleCollection(Model):
    name: str = "Modules"
    dataset_id: int | str | None = None
    modules: list[Module] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.MODULE_COLLECTION, init=False)

    def node_key(self) -> str:
        return f"{self.kind}:dataset:{self.dataset_id}"
