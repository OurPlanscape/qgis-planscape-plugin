from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from planscape.models.api.dataset import BrowseDatasetResponse, DatasetPayloadError
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import fetch

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.api.dataset import BrowseDatasetTree


DATASETS_PATH = "/v2/datasets/"
logger = logging.getLogger(__name__)


class DatasetApiError(Exception):
    pass


def browse_dataset_request(base_url: str, authcfg_id: str, dataset_id: int | str) -> BrowseDatasetTree:
    url = _dataset_browse_url(base_url, dataset_id)
    logger.info("[API] GET:%s", url)
    response = _request_json_list(
        lambda: fetch(url, authcfg_id=authcfg_id),
        "Planscape dataset browse request failed",
    )

    try:
        return BrowseDatasetResponse.from_list(response).to_tree()
    except DatasetPayloadError as exc:
        message = "Planscape returned an invalid dataset browse response."
        raise DatasetApiError(message) from exc


def _request_json_list(request: Callable[[], str], failure_message: str) -> list[object]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise DatasetApiError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON dataset response."
        raise DatasetApiError(message) from exc

    if not isinstance(body, list):
        message = "Planscape returned an invalid dataset browse response."
        raise DatasetApiError(message)
    return body


def _dataset_browse_url(base_url: str, dataset_id: int | str) -> str:
    return f"{base_url}{DATASETS_PATH}{dataset_id}/browse/"
