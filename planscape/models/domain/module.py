from __future__ import annotations

from dataclasses import dataclass, field

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind


@dataclass
class Module(Model):
    kind: NodeKind = field(default=NodeKind.MODULE, init=False)
