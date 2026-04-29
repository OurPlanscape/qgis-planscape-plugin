from __future__ import annotations

from dataclasses import dataclass, field

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind


@dataclass
class Style(Model):
    kind: NodeKind = field(default=NodeKind.STYLE, init=False)
