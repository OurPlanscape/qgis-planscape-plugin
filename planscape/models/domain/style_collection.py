from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind

if TYPE_CHECKING:
    from planscape.models.domain.style import Style


@dataclass
class StyleCollection(Model):
    name: str = "Styles"
    workspace_id: int | str | None = None
    styles: list[Style] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.STYLE_COLLECTION, init=False)

    def node_key(self) -> str:
        return f"{self.kind}:workspace:{self.workspace_id}"
