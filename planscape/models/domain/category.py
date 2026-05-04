from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.datalayer import DataLayer


@dataclass
class Category(Model):
    path: list[str] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    datalayers: list[DataLayer] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.CATEGORY, init=False)

    def node_key(self) -> str:
        identity = "/".join(self.path) if self.path else self.node_label()
        return f"{self.kind}:{identity}"
