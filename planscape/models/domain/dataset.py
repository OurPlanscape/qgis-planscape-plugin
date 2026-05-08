from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind
from planscape.models.domain.workspace import WorkspaceVisibility

if TYPE_CHECKING:
    from planscape.models.domain.category import Category
    from planscape.models.domain.datalayer import DataLayer


@dataclass
class Dataset(Model):
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    modules: str = ""
    datalayers: list[DataLayer] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.DATASET, init=False)
