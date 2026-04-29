from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.category import Category


@dataclass
class CategoryCollection(Model):
    name: str = "Categories"
    dataset_id: int | str | None = None
    categories: List[Category] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.CATEGORY_COLLECTION, init=False)

    def node_key(self) -> str:
        return f"{self.kind}:dataset:{self.dataset_id}"
