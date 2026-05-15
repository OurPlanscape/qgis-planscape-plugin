from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind
from planscape.models.domain.workspace import WorkspaceVisibility

if TYPE_CHECKING:
    from planscape.models.domain.category import Category
    from planscape.models.domain.datalayer import DataLayer


class DatasetPreferredDisplayType(StrEnum):
    MAIN_DATALAYERS = "MAIN_DATALAYERS"
    BASE_DATALAYERS = "BASE_DATALAYERS"


class DatasetSelectionType(StrEnum):
    SINGLE = "SINGLE"
    MULTIPLE = "MULTIPLE"


@dataclass
class Dataset(Model):
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    preferred_display_type: DatasetPreferredDisplayType = DatasetPreferredDisplayType.MAIN_DATALAYERS
    selection_type: DatasetSelectionType = DatasetSelectionType.SINGLE
    modules: list[str] = field(default_factory=list)
    datalayers: list[DataLayer] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.DATASET, init=False)
