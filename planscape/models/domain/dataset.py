from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.category import Category
    from planscape.models.domain.datalayer import DataLayer


@dataclass
class Dataset(Model):
    datalayers: List[DataLayer] = field(default_factory=list)
    categories: List[Category] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.DATASET, init=False)
