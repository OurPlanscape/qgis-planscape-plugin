from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from planscape.models.domain.auth import AuthErrorDetails


class PlanscapeError(Exception):
    pass


class PlanscapeAPIError(PlanscapeError):
    pass


class PlanscapePayloadError(PlanscapeError):
    pass


class AuthAPIError(PlanscapeAPIError):
    def __init__(self, message: str, error_details: AuthErrorDetails | None = None) -> None:
        super().__init__(message)
        self.error_details = error_details


class DataLayerAPIError(PlanscapeAPIError):
    pass


class DatasetAPIError(PlanscapeAPIError):
    pass


class WorkspaceAPIError(PlanscapeAPIError):
    pass


class StyleAPIError(PlanscapeAPIError):
    pass


class DatasetPayloadError(PlanscapePayloadError):
    pass


class DataLayerPayloadError(PlanscapePayloadError):
    pass


class WorkspacePayloadError(PlanscapePayloadError):
    pass


class StylePayloadError(PlanscapePayloadError):
    pass
