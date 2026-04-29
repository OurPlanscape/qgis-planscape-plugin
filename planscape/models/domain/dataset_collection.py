from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.dataset import Dataset


@dataclass
class DatasetCollection(Model):
    name: str = "Datasets"
    workspace_id: int | str | None = None
    datasets: list[Dataset] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.DATASET_COLLECTION, init=False)

    def node_key(self) -> str:
        return f"{self.kind}:workspace:{self.workspace_id}"
