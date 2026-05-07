from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from planscape.models.domain.auth import AuthErrorDetails


class AuthApiError(Exception):
    def __init__(self, message: str, error_details: AuthErrorDetails | None = None) -> None:
        super().__init__(message)
        self.error_details = error_details


class DataLayerApiError(Exception):
    pass


class DatasetApiError(Exception):
    pass


class WorkspaceApiError(Exception):
    pass
