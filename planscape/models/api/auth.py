from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from planscape.models.domain.auth import AuthErrorDetails


class AuthPayloadError(Exception):
    pass


@dataclass(frozen=True)
class LoginErrorPayload:
    detail: str = ""
    non_field_errors: List[str] = field(default_factory=list)
    field_errors: dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LoginErrorPayload:
        if not isinstance(payload, dict):
            message = "Login error payload must be an object."
            raise AuthPayloadError(message)

        detail = _optional_string(payload.get("detail"), "detail")
        non_field_errors = _string_list(payload.get("non_field_errors", []), "non_field_errors")

        field_errors: dict[str, List[str]] = {}
        for key, value in payload.items():
            if key in {"detail", "non_field_errors"}:
                continue
            field_errors[key] = _string_list(value, key)

        return cls(detail=detail, non_field_errors=non_field_errors, field_errors=field_errors)

    def to_domain(self) -> AuthErrorDetails:
        detail = self.detail or "\n".join(self.non_field_errors)
        return AuthErrorDetails(detail=detail, field_errors=self.field_errors)


def _optional_string(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    message = f"{field_name} must be a string."
    raise AuthPayloadError(message)


def _string_list(value: Any, field_name: str) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    message = f"{field_name} must be a string or list of strings."
    raise AuthPayloadError(message)
