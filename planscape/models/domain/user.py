from __future__ import annotations

from dataclasses import dataclass, field

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind


@dataclass
class User(Model):
    email: str = ""
    kind: NodeKind = field(default=NodeKind.USER, init=False)
