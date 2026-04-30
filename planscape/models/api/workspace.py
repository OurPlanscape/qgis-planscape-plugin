from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from planscape.models.domain.workspace import Workspace, WorkspaceVisibility


class WorkspacePayloadError(Exception):
    pass


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


def _required_string(value: Any, field_name: str) -> str:
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string."
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
