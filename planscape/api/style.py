from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from planscape.api.common import log_api_failure, log_api_success
from planscape.api.exceptions import StyleAPIError, StylePayloadError
from planscape.models.api.style import StyleResponse
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import post

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.api.style import CreateStyleRequest
    from planscape.models.domain.style import Style


ADMIN_STYLES_PATH = "/v2/admin/styles/"
logger = logging.getLogger(__name__)


def create_style_request(base_url: str, authcfg_id: str, request: CreateStyleRequest) -> Style:
    url = _admin_styles_url(base_url)
    try:
        response = _request_json(
            lambda: post(url, authcfg_id=authcfg_id, data=request.to_dict()),  # type: ignore[arg-type]
            "Planscape style create request failed",
        )
        result = StyleResponse.from_dict(response).to_domain()
    except Exception as exc:
        log_api_failure(logger, "POST", url, exc)
        raise
    else:
        log_api_success(logger, "POST", url)
        return result


def _request_json(request: Callable[[], str], failure_message: str) -> dict[str, Any]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise StyleAPIError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON style response."
        raise StylePayloadError(message) from exc

    if not isinstance(body, dict):
        message = "Planscape returned an invalid style response."
        raise StylePayloadError(message)
    return body


def _admin_styles_url(base_url: str) -> str:
    return f"{base_url}{ADMIN_STYLES_PATH}"
