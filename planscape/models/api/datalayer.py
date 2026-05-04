from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class DataLayerPayloadError(Exception):
    pass


@dataclass(frozen=True)
class DataLayerUrlsResponse:
    layer_url: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DataLayerUrlsResponse:
        if not isinstance(payload, dict):
            message = "Datalayer URLs response must be an object."
            raise DataLayerPayloadError(message)
        return cls(layer_url=_required_string(payload.get("layer_url"), "layer_url"))


def _required_string(value: Any, field_name: str) -> str:
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string."
    raise DataLayerPayloadError(message)
