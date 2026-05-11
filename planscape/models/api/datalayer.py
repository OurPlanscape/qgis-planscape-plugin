from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from planscape.api.exceptions import DataLayerPayloadError
from planscape.models.domain.datalayer import DataLayer


@dataclass(frozen=True)
class CreateDataLayerRequest:
    name: str
    dataset: int | str
    organization: int
    layer_info: dict[str, Any]
    metadata: dict[str, Any] | None = None
    category: int | None = None
    original_name: str | None = None
    mimetype: str | None = "image/tiff"
    style: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization": self.organization,
            "name": self.name,
            "dataset": self.dataset,
            "category": self.category,
            "type": "RASTER",
            "info": self.layer_info,
            "metadata": self.metadata or {},
            "original_name": self.original_name,
            "mimetype": self.mimetype,
            "geometry_type": "RASTER",
            "style": self.style,
            "map_service_type": "COG",
            "url": None,
        }


@dataclass(frozen=True)
class DataLayerUploadTarget:
    url: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DataLayerUploadTarget | None:
        if not payload:
            return None
        url = payload.get("url")
        if not isinstance(url, str):
            message = "upload_to.url must be a string."
            raise DataLayerPayloadError(message)
        return cls(url=url)


@dataclass(frozen=True)
class CreateDataLayerResponse:
    datalayer: DataLayer
    upload_to: DataLayerUploadTarget | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CreateDataLayerResponse:
        if not isinstance(payload, dict):
            message = "Datalayer create response must be an object."
            raise DataLayerPayloadError(message)
        datalayer_payload = payload.get("datalayer")
        if not isinstance(datalayer_payload, dict):
            message = "datalayer must be an object."
            raise DataLayerPayloadError(message)
        return cls(
            datalayer=DataLayer(
                id=_required_int(datalayer_payload.get("id"), "datalayer.id"),
                name=_required_string(datalayer_payload.get("name"), "datalayer.name"),
                type=_optional_string(datalayer_payload.get("type"), "datalayer.type"),
                status=_optional_string(datalayer_payload.get("status"), "datalayer.status"),
                map_service_type=_optional_string(
                    datalayer_payload.get("map_service_type"),
                    "datalayer.map_service_type",
                ),
                info=datalayer_payload.get("info"),
                metadata=datalayer_payload.get("metadata"),
            ),
            upload_to=DataLayerUploadTarget.from_dict(payload.get("upload_to") or {}),
        )


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


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _required_string(value, field_name)


def _required_int(value: Any, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    message = f"{field_name} must be an integer."
    raise DataLayerPayloadError(message)
