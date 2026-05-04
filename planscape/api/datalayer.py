from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from planscape.models.api.datalayer import DataLayerPayloadError, DataLayerUrlsResponse
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import fetch

if TYPE_CHECKING:
    from collections.abc import Callable


DATALAYERS_PATH = "/v2/datalayers/"
logger = logging.getLogger(__name__)


class DataLayerApiError(Exception):
    pass


def retrieve_datalayer_urls_request(base_url: str, authcfg_id: str, datalayer_id: int) -> DataLayerUrlsResponse:
    url = _datalayer_urls_url(base_url, datalayer_id)
    logger.info("[API] GET:%s", url)
    response = _request_json(
        lambda: fetch(url, authcfg_id=authcfg_id),
        "Planscape datalayer URLs request failed",
    )

    try:
        return DataLayerUrlsResponse.from_dict(response)
    except DataLayerPayloadError as exc:
        message = "Planscape returned an invalid datalayer URLs response."
        raise DataLayerApiError(message) from exc


def _request_json(request: Callable[[], str], failure_message: str) -> dict[str, object]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise DataLayerApiError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON datalayer response."
        raise DataLayerApiError(message) from exc

    if not isinstance(body, dict):
        message = "Planscape returned an invalid datalayer response."
        raise DataLayerApiError(message)
    return body


def _datalayer_urls_url(base_url: str, datalayer_id: int | str) -> str:
    return f"{base_url}{DATALAYERS_PATH}{datalayer_id}/urls/"
