from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from planscape.api.common import log_api_failure, log_api_success
from planscape.api.exceptions import DatasetAPIError, DatasetPayloadError
from planscape.models.api.dataset import BrowseDatasetResponse, DatasetResponse
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.network import fetch, post
from planscape.tools.network import put

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.api.dataset import BrowseDatasetTree, CreateDatasetRequest, UpdateDatasetRequest
    from planscape.models.domain.dataset import Dataset


DATASETS_PATH = "/v2/datasets/"
ADMIN_DATASETS_PATH = "/v2/admin/datasets/"
logger = logging.getLogger(__name__)


def create_dataset_request(base_url: str, authcfg_id: str, request: CreateDatasetRequest) -> Dataset:
    url = _admin_datasets_url(base_url)
    try:
        response = _request_json(
            lambda: post(url, authcfg_id=authcfg_id, data=request.to_dict()),  # type: ignore
            "Planscape dataset create request failed",
        )
        result = _dataset_from_response(response)
    except Exception as exc:
        log_api_failure(logger, "POST", url, exc)
        raise
    else:
        log_api_success(logger, "POST", url)
        return result


def update_dataset_request(
    base_url: str,
    authcfg_id: str,
    dataset_id: int | str,
    request: UpdateDatasetRequest,
) -> Dataset:
    url = _admin_dataset_url(base_url, dataset_id)
    try:
        response = _request_json(
            lambda: put(url, authcfg_id=authcfg_id, data=request.to_dict()),
            "Planscape dataset update request failed",
        )
        result = _dataset_from_response(response)
    except Exception as exc:
        log_api_failure(logger, "PUT", url, exc)
        raise
    else:
        log_api_success(logger, "PUT", url)
        return result


def browse_dataset_request(base_url: str, authcfg_id: str, dataset_id: int | str) -> BrowseDatasetTree:
    url = _dataset_browse_url(base_url, dataset_id)
    try:
        response = _request_json_list(
            lambda: fetch(url, authcfg_id=authcfg_id),
            "Planscape dataset browse request failed",
        )
        result = BrowseDatasetResponse.from_list(response).to_tree()
    except Exception as exc:
        log_api_failure(logger, "GET", url, exc)
        raise
    else:
        log_api_success(logger, "GET", url)
        return result


def _dataset_from_response(response: dict[str, Any]) -> Dataset:
    return DatasetResponse.from_dict(response).to_domain()


def _request_json(request: Callable[[], str], failure_message: str) -> dict[str, Any]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise DatasetAPIError(message) from exc

    try:
        return json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON dataset response."
        raise DatasetPayloadError(message) from exc


def _request_json_list(request: Callable[[], str], failure_message: str) -> list[object]:
    try:
        response = request()
    except QgsPluginException as exc:
        message = f"{failure_message}: {exc}"
        raise DatasetAPIError(message) from exc

    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        message = "Planscape returned an invalid JSON dataset response."
        raise DatasetPayloadError(message) from exc

    return body


def _dataset_browse_url(base_url: str, dataset_id: int | str) -> str:
    return f"{base_url}{DATASETS_PATH}{dataset_id}/browse/"


def _admin_datasets_url(base_url: str) -> str:
    return f"{base_url}{ADMIN_DATASETS_PATH}"


def _admin_dataset_url(base_url: str, dataset_id: int | str) -> str:
    return f"{_admin_datasets_url(base_url)}{dataset_id}/"
