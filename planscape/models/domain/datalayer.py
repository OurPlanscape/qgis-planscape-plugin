from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from planscape.models.domain.model import Model
from planscape.models.domain.node_kind import NodeKind


@dataclass
class DataLayer(Model):
    path: list[str] = field(default_factory=list)
    type: str | None = None
    map_url: str | None = None
    geometry_type: str | None = None
    status: str | None = None
    storage_type: str | None = None
    map_service_type: str | None = None
    info: Any = None
    metadata: Any = None
    styles: list[Any] = field(default_factory=list)
    kind: NodeKind = field(default=NodeKind.DATALAYER, init=False)
