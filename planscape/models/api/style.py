from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from planscape.api.exceptions import StylePayloadError
from planscape.models.domain.style import Style


@dataclass(frozen=True)
class CreateStyleRequest:
    name: str
    data: dict[str, Any]
    organization: int
    datalayers: list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "type": "RASTER",
            "data": self.data,
            "organization": self.organization,
        }
        if self.datalayers:
            payload["datalayers"] = list(self.datalayers)
        return payload


@dataclass(frozen=True)
class StyleResponse:
    id: int
    name: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StyleResponse:
        if not isinstance(payload, dict):
            message = "Style response must be an object."
            raise StylePayloadError(message)
        if isinstance(payload.get("style"), dict):
            payload = payload["style"]
        return cls(
            id=_required_int(payload.get("id"), "id"),
            name=_required_string(payload.get("name"), "name"),
        )

    def to_domain(self) -> Style:
        return Style(id=self.id, name=self.name)


def _required_string(value: Any, field_name: str) -> str:
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string."
    raise StylePayloadError(message)


def _required_int(value: Any, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    message = f"{field_name} must be an integer."
    raise StylePayloadError(message)
