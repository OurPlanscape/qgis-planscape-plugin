from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from planscape.api.exceptions import DatasetPayloadError
from planscape.models.domain.category import Category
from planscape.models.domain.datalayer import DataLayer
from planscape.models.domain.dataset import Dataset
from planscape.models.domain.workspace import WorkspaceVisibility


@dataclass(frozen=True)
class CreateDatasetRequest:
    workspace_id: int | str
    name: str
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    organization: int | None = None
    version: str | None = None
    modules: str = "forsys,map,prioritize_sub_units"

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "visibility": self.visibility.value,
            "modules": _modules_to_list(self.modules),
        }
        if self.organization is not None:
            payload["organization"] = self.organization
        if self.version is not None:
            payload["version"] = self.version
        return payload


@dataclass(frozen=True)
class UpdateDatasetRequest:
    name: str | None = None
    visibility: WorkspaceVisibility | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {}
        if self.name is not None:
            payload["name"] = self.name
        if self.visibility is not None:
            payload["visibility"] = self.visibility.value
        return payload


@dataclass(frozen=True)
class DatasetResponse:
    name: str
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    id: int | None = None
    modules: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DatasetResponse:
        return cls(
            id=_optional_int(payload.get("id"), "id"),
            name=_required_string(payload.get("name"), "name"),
            visibility=_visibility(payload.get("visibility", WorkspaceVisibility.PRIVATE.value)),
            modules=_modules_to_string(payload.get("modules")),
        )

    def to_domain(self) -> Dataset:
        return Dataset(id=self.id, name=self.name, visibility=self.visibility, modules=self.modules)


@dataclass(frozen=True)
class BrowseDatasetResponse:
    datalayers: list[DataLayer] = field(default_factory=list)

    @classmethod
    def from_list(cls, payload: list[Any]) -> BrowseDatasetResponse:
        if not isinstance(payload, list):
            message = "Browse dataset response must be a list."
            raise DatasetPayloadError(message)
        return cls(datalayers=[BrowseDataLayerResponse.from_dict(item).to_domain() for item in payload])

    def to_tree(self) -> BrowseDatasetTree:
        root_categories: list[Category] = []
        root_datalayers: list[DataLayer] = []
        category_index: dict[tuple[str, ...], Category] = {}

        for datalayer in self.datalayers:
            if not datalayer.path:
                root_datalayers.append(datalayer)
                continue

            parent_categories = root_categories
            current_path: list[str] = []
            category = None
            for category_name in datalayer.path:
                current_path.append(category_name)
                path_key = tuple(current_path)
                category = category_index.get(path_key)
                if category is None:
                    category = Category(name=category_name, path=list(current_path))
                    category_index[path_key] = category
                    parent_categories.append(category)
                parent_categories = category.categories

            if category is None:
                root_datalayers.append(datalayer)
            else:
                category.datalayers.append(datalayer)

        return BrowseDatasetTree(categories=root_categories, datalayers=root_datalayers)


@dataclass(frozen=True)
class BrowseDatasetTree:
    categories: list[Category] = field(default_factory=list)
    datalayers: list[DataLayer] = field(default_factory=list)


@dataclass(frozen=True)
class BrowseDataLayerResponse:
    id: int
    name: str
    path: list[str]
    type: str
    map_url: str | None = None
    geometry_type: str | None = None
    status: str | None = None
    storage_type: str | None = None
    map_service_type: str | None = None
    info: Any = None
    metadata: Any = None
    styles: list[Any] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BrowseDataLayerResponse:
        if not isinstance(payload, dict):
            message = "Browse datalayer response must be an object."
            raise DatasetPayloadError(message)

        return cls(
            id=_required_int(payload.get("id"), "id"),
            name=_required_string(payload.get("name"), "name"),
            path=_required_string_list(payload.get("path"), "path"),
            type=_required_string(payload.get("type"), "type"),
            map_url=_optional_string(payload.get("map_url"), "map_url"),
            geometry_type=_optional_string(payload.get("geometry_type"), "geometry_type"),
            status=_optional_string(payload.get("status"), "status"),
            storage_type=_optional_string(payload.get("storage_type"), "storage_type"),
            map_service_type=_optional_string(payload.get("map_service_type"), "map_service_type"),
            info=payload.get("info"),
            metadata=payload.get("metadata"),
            styles=_optional_list(payload.get("styles"), "styles"),
        )

    def to_domain(self) -> DataLayer:
        return DataLayer(
            id=self.id,
            name=self.name,
            path=list(self.path),
            type=self.type,
            map_url=self.map_url,
            geometry_type=self.geometry_type,
            status=self.status,
            storage_type=self.storage_type,
            map_service_type=self.map_service_type,
            info=self.info,
            metadata=self.metadata,
            styles=list(self.styles),
        )


def _required_string(value: Any, field_name: str) -> str:
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string."
    raise DatasetPayloadError(message)


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string or null."
    raise DatasetPayloadError(message)


def _required_int(value: Any, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    message = f"{field_name} must be an integer."
    raise DatasetPayloadError(message)


def _optional_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    return _required_int(value, field_name)


def _visibility(value: Any) -> WorkspaceVisibility:
    if isinstance(value, WorkspaceVisibility):
        return value
    if isinstance(value, str):
        try:
            return WorkspaceVisibility(value)
        except ValueError as exc:
            message = f"Unsupported dataset visibility: {value}"
            raise DatasetPayloadError(message) from exc
    message = "visibility must be a string."
    raise DatasetPayloadError(message)


def _required_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        message = f"{field_name} must be a list of strings."
        raise DatasetPayloadError(message)
    return list(value)


def _optional_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    message = f"{field_name} must be a list or null."
    raise DatasetPayloadError(message)


def _modules_to_list(value: str) -> list[str]:
    return [module.strip() for module in value.split(",") if module.strip()]


def _modules_to_string(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        message = "modules must be a list of strings or null."
        raise DatasetPayloadError(message)
    return ",".join(value)
