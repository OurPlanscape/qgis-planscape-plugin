from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from planscape.api.exceptions import WorkspacePayloadError
from planscape.models.domain.dataset import Dataset
from planscape.models.domain.style import Style
from planscape.models.domain.user import User
from planscape.models.domain.workspace import Workspace, WorkspaceVisibility


@dataclass(frozen=True)
class CreateWorkspaceRequest:
    name: str
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "visibility": self.visibility.value}


@dataclass(frozen=True)
class UpdateWorkspaceRequest:
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
class WorkspaceResponse:
    name: str
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkspaceResponse:
        if not isinstance(payload, dict):
            message = "Workspace response must be an object."
            raise WorkspacePayloadError(message)

        return cls(
            id=_optional_int(payload.get("id"), "id"),
            name=_required_string(payload.get("name"), "name"),
            visibility=_visibility(payload.get("visibility", WorkspaceVisibility.PRIVATE.value)),
            created_at=_optional_string(payload.get("created_at"), "created_at"),
            updated_at=_optional_string(payload.get("updated_at"), "updated_at"),
            deleted_at=_optional_string(payload.get("deleted_at"), "deleted_at"),
        )

    def to_domain(self) -> Workspace:
        return Workspace(id=self.id, name=self.name, visibility=self.visibility)


@dataclass(frozen=True)
class PaginatedWorkspaceResponse:
    count: int
    results: list[WorkspaceResponse] = field(default_factory=list)
    next: str | None = None
    previous: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PaginatedWorkspaceResponse:
        if not isinstance(payload, dict):
            message = "Paginated workspace response must be an object."
            raise WorkspacePayloadError(message)

        results = payload.get("results")
        if not isinstance(results, list):
            message = "results must be a list."
            raise WorkspacePayloadError(message)

        return cls(
            count=_required_int(payload.get("count"), "count"),
            next=_optional_string(payload.get("next"), "next"),
            previous=_optional_string(payload.get("previous"), "previous"),
            results=[WorkspaceResponse.from_dict(item) for item in results],
        )

    def to_domain(self) -> list[Workspace]:
        return [workspace.to_domain() for workspace in self.results]


@dataclass(frozen=True)
class WorkspaceDatasetResponse:
    id: int
    name: str
    visibility: WorkspaceVisibility = WorkspaceVisibility.PRIVATE
    modules: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkspaceDatasetResponse:
        if not isinstance(payload, dict):
            message = "Workspace dataset response must be an object."
            raise WorkspacePayloadError(message)

        return cls(
            id=_required_int(payload.get("id"), "id"),
            name=_required_string(payload.get("name"), "name"),
            visibility=_visibility(payload.get("visibility", WorkspaceVisibility.PRIVATE.value)),
            modules=_modules_to_list(payload.get("modules")),
        )

    def to_domain(self) -> Dataset:
        return Dataset(id=self.id, name=self.name, visibility=self.visibility, modules=self.modules)


@dataclass(frozen=True)
class WorkspaceStyleResponse:
    id: int
    name: str
    type: str = "RASTER"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkspaceStyleResponse:
        if not isinstance(payload, dict):
            message = "Workspace style response must be an object."
            raise WorkspacePayloadError(message)

        return cls(
            id=_required_int(payload.get("id"), "id"),
            name=_required_string(payload.get("name"), "name"),
            type=_optional_string(payload.get("type"), "type") or "RASTER",
        )

    def to_domain(self) -> Style:
        return Style(id=self.id, name=self.name)


@dataclass(frozen=True)
class WorkspaceUserAccessResponse:
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str = "VIEWER"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkspaceUserAccessResponse:
        if not isinstance(payload, dict):
            message = "Workspace user access response must be an object."
            raise WorkspacePayloadError(message)

        return cls(
            user_id=_required_int(payload.get("user_id"), "user_id"),
            email=_required_string(payload.get("email"), "email"),
            first_name=_required_string(payload.get("first_name"), "first_name"),
            last_name=_required_string(payload.get("last_name"), "last_name"),
            role=_optional_string(payload.get("role"), "role") or "VIEWER",
        )

    def to_domain(self) -> User:
        name = f"{self.first_name} {self.last_name}".strip() or self.email
        return User(id=self.user_id, name=name, email=self.email)


@dataclass(frozen=True)
class WorkspaceDatasetListResponse:
    results: list[WorkspaceDatasetResponse] = field(default_factory=list)

    @classmethod
    def from_list(cls, payload: list[Any]) -> WorkspaceDatasetListResponse:
        if not isinstance(payload, list):
            message = "Workspace dataset list response must be a list."
            raise WorkspacePayloadError(message)
        return cls(results=[WorkspaceDatasetResponse.from_dict(item) for item in payload])

    def to_domain(self) -> list[Dataset]:
        return [dataset.to_domain() for dataset in self.results]


@dataclass(frozen=True)
class WorkspaceStyleListResponse:
    results: list[WorkspaceStyleResponse] = field(default_factory=list)

    @classmethod
    def from_list(cls, payload: list[Any]) -> WorkspaceStyleListResponse:
        if not isinstance(payload, list):
            message = "Workspace style list response must be a list."
            raise WorkspacePayloadError(message)
        return cls(results=[WorkspaceStyleResponse.from_dict(item) for item in payload])

    def to_domain(self) -> list[Style]:
        return [style.to_domain() for style in self.results]


@dataclass(frozen=True)
class WorkspaceUserAccessListResponse:
    results: list[WorkspaceUserAccessResponse] = field(default_factory=list)

    @classmethod
    def from_list(cls, payload: list[Any]) -> WorkspaceUserAccessListResponse:
        if not isinstance(payload, list):
            message = "Workspace user access list response must be a list."
            raise WorkspacePayloadError(message)
        return cls(results=[WorkspaceUserAccessResponse.from_dict(item) for item in payload])

    def to_domain(self) -> list[User]:
        return [user.to_domain() for user in self.results]


def _required_string(value: Any, field_name: str) -> str:
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string."
    raise WorkspacePayloadError(message)


def _modules_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [module.strip() for module in value.split(",") if module.strip()]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    message = "modules must be a list of strings, string, or null."
    raise WorkspacePayloadError(message)


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string or null."
    raise WorkspacePayloadError(message)


def _required_int(value: Any, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    message = f"{field_name} must be an integer."
    raise WorkspacePayloadError(message)


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
            message = f"Unsupported workspace visibility: {value}"
            raise WorkspacePayloadError(message) from exc
    message = "visibility must be a string."
    raise WorkspacePayloadError(message)
