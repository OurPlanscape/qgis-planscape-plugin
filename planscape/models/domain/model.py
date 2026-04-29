from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from planscape.models.domain.node_kind import NodeKind


@dataclass
class Model:
    name: str = ""
    id: int | str | None = None
    kind: NodeKind = field(init=False)

    def node_label(self) -> str:
        return self.name

    def node_key(self) -> str:
        identity = self.id if self.id is not None else self.node_label()
        return f"{self.kind}:{identity}"
