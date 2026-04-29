from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.workspace import Workspace


@dataclass
class Server(Model):
    name: str = "Planscape"
    env: str = "dev"
    workspaces: List[Workspace] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.SERVER, init=False)

    def node_label(self) -> str:
        return f"{self.name} ({self.env})"
