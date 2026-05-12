from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from planscape.api.common import log_api_failure, log_api_success
from planscape.api.exceptions import DataLayerAPIError, DataLayerPayloadError
from planscape.models.api.datalayer import CreateDataLayerResponse, DataLayerUrlsResponse
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import fetch, post

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.api.datalayer import CreateDataLayerRequest


DATALAYERS_PATH = "/v2/datalayers/"
ADMIN_DATALAYERS_PATH = "/v2/admin/datalayers/"
logger = logging.getLogger(__name__)


def create_datalayer_request(
    base_url: str,
    authcfg_id: str,
    request: CreateDataLayerRequest,
) -> CreateDataLayerResponse:
    url = _admin_datalayers_url(base_url)
    try:
        response = _request_json(
            lambda: post(url, authcfg_id=authcfg_id, data=request.to_dict()),  # type: ignore[arg-type]
            "Planscape datalayer create request failed",
        )
        result = CreateDataLayerResponse.from_dict(response)
    except Exception as exc:
        log_api_failure(logger, "POST", url, exc)
        raise
    else:
        log_api_success(logger, "POST", url)
        return result


def update_datalayer_status_request(
    base_url: str,
    authcfg_id: str,
    datalayer_id: int | str,
    organization: int,
    status: str,
) -> dict[str, object]:
    url = _admin_datalayer_change_status_url(base_url, datalayer_id)
    try:
        response = _request_json(
            lambda: post(
                url,
                authcfg_id=authcfg_id,
                data={"organization": organization, "status": status},
            ),
            "Planscape datalayer status update request failed",
        )
    except Exception as exc:
        log_api_failure(logger, "POST", url, exc)
        raise
    else:
        log_api_success(logger, "POST", url)
        return response


def retrieve_datalayer_urls_request(base_url: str, authcfg_id: str, datalayer_id: int) -> DataLayerUrlsResponse:
    url = _datalayer_urls_url(base_url, datalayer_id)
    try:
        response = _request_json(
            lambda: fetch(url, authcfg_id=authcfg_id),
            "Planscape datalayer URLs request failed",
        )
        result = DataLayerUrlsResponse.from_dict(response)
    except Exception as exc:
        log_api_failure(logger, "GET", url, exc)
        raise
    else:
        log_api_success(logger, "GET", url)
        return result


def _request_json(request: Callable[[], str], failure_message: str) -> dict[str, object]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise DataLayerAPIError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON datalayer response."
        raise DataLayerAPIError(message) from exc

    if not isinstance(body, dict):
        message = "Planscape returned an invalid datalayer response."
        raise DataLayerPayloadError(message)
    return body


def _datalayer_urls_url(base_url: str, datalayer_id: int | str) -> str:
    return f"{base_url}{DATALAYERS_PATH}{datalayer_id}/urls/"


def _admin_datalayers_url(base_url: str) -> str:
    return f"{base_url}{ADMIN_DATALAYERS_PATH}"


def _admin_datalayer_change_status_url(base_url: str, datalayer_id: int | str) -> str:
    return f"{_admin_datalayers_url(base_url)}{datalayer_id}/change_status/"
