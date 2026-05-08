from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from planscape.api.common import log_api_failure, log_api_success
from planscape.api.exceptions import AuthAPIError
from planscape.models.api.auth import AuthPayloadError, LoginErrorPayload
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import post

if TYPE_CHECKING:
    from planscape.models.domain.auth import AuthErrorDetails

LOGIN_PATH = "/dj-rest-auth/login/"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoginTokens:
    access_token: str
    refresh_token: str


def sign_in_request(email: str, password: str, base_url: str) -> LoginTokens:
    url = f"{base_url}{LOGIN_PATH}"
    try:
        response = post(
            url,
            data={
                "email": email,
                "username": email,
                "password": password,
            },
        )
    except QgsPluginException as exc:
        error_details = _parse_login_error(str(exc))
        message = error_details.formatted_message() if error_details else str(exc)
        api_error = AuthAPIError(message, error_details)
        log_api_failure(logger, "POST", url, api_error)
        raise api_error from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid login response."
        api_error = AuthAPIError(message)
        log_api_failure(logger, "POST", url, api_error)
        raise api_error from exc

    access_token = body.get("access")
    refresh_token = body.get("refresh")
    if not isinstance(access_token, str) or not access_token:
        message = "Planscape login did not return an access token."
        api_error = AuthAPIError(message)
        log_api_failure(logger, "POST", url, api_error)
        raise api_error
    if not isinstance(refresh_token, str) or not refresh_token:
        message = "Planscape login did not return a refresh token."
        api_error = AuthAPIError(message)
        log_api_failure(logger, "POST", url, api_error)
        raise api_error

    log_api_success(logger, "POST", url)
    return LoginTokens(access_token=access_token, refresh_token=refresh_token)


def _parse_login_error(response: str) -> AuthErrorDetails | None:
    try:
        body = json.loads(response)
        return LoginErrorPayload.from_dict(body).to_domain()
    except (json.JSONDecodeError, AuthPayloadError):
        return None
