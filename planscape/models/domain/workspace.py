from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.dataset import Dataset
    from planscape.models.domain.style import Style
    from planscape.models.domain.user import User


class WorkspaceVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


@dataclass
class Workspace(Model):
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    dataset_count: int | None = None
    style_count: int | None = None
    user_count: int | None = None
    datasets: list[Dataset] = field(default_factory=list)
    styles: list[Style] = field(default_factory=list)
    users: list[User] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.WORKSPACE, init=False)
