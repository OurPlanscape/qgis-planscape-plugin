from __future__ import annotations

import logging
from time import perf_counter
from typing import TYPE_CHECKING

from qgis.core import (
    QgsColorRampShader,
    QgsProject,
    QgsRasterLayer,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsVectorTileLayer,
)
from qgis.PyQt.QtGui import QColor

from planscape import auth
from planscape.api.datalayer import retrieve_datalayer_urls_request
from planscape.api.exceptions import DataLayerAPIError

if TYPE_CHECKING:
    from planscape.models.domain import DataLayer

logger = logging.getLogger(__name__)
LAYER_NAME_PREFIX = "[PS]"


def add_datalayer_to_project(datalayer: DataLayer) -> None:
    started_at = perf_counter()
    if datalayer.id is None:
        return

    project = QgsProject.instance()
    layer_name = _qgis_layer_name(datalayer)
    if _project_has_layer(project, layer_name):
        logger.info("Datalayer already exists in QGIS project: %s", layer_name)
        return

    layer_url = _datalayer_url(datalayer)
    if layer_url is None:
        return

    layer_started_at = perf_counter()
    layer = _qgis_layer(datalayer, layer_url, layer_name)
    logger.info("Datalayer QGIS layer construction took %.3fs", perf_counter() - layer_started_at)

    valid_started_at = perf_counter()
    if not layer.isValid():
        logger.info("Datalayer QGIS layer validation took %.3fs", perf_counter() - valid_started_at)
        logger.info("QGIS rejected datalayer URL for %s", datalayer.node_label())
        return
    logger.info("Datalayer QGIS layer validation took %.3fs", perf_counter() - valid_started_at)

    style_started_at = perf_counter()
    _apply_datalayer_style(datalayer, layer)
    logger.info("Datalayer style application took %.3fs", perf_counter() - style_started_at)

    add_started_at = perf_counter()
    project.addMapLayer(layer)
    logger.info("Datalayer project add took %.3fs", perf_counter() - add_started_at)
    logger.info("Datalayer add total took %.3fs", perf_counter() - started_at)


def _datalayer_url(datalayer: DataLayer) -> str | None:
    if datalayer.map_url:
        logger.info("Using datalayer map_url from browse payload")
        return datalayer.map_url
    if not isinstance(datalayer.id, int) or isinstance(datalayer.id, bool):
        return None

    started_at = perf_counter()
    try:
        urls = retrieve_datalayer_urls_request(
            auth.get_base_url(auth.get_environment()),
            auth.ensure_authenticated(),
            datalayer.id,
        )
    except DataLayerAPIError as exc:
        logger.info("Failed to retrieve datalayer URLs: %s", exc)
        return None
    logger.info("Datalayer URLs request took %.3fs", perf_counter() - started_at)
    return urls.layer_url


def _qgis_layer(datalayer: DataLayer, layer_url: str, layer_name: str):
    if datalayer.type == "RASTER" or datalayer.map_service_type == "COG":
        return QgsRasterLayer(layer_url, layer_name, "gdal")
    return QgsVectorTileLayer(f"type=xyz&url={layer_url}", layer_name)


def _qgis_layer_name(datalayer: DataLayer) -> str:
    return f"{LAYER_NAME_PREFIX} {datalayer.node_label()}"


def _project_has_layer(project: QgsProject, layer_name: str) -> bool:
    return any(layer.name() == layer_name for layer in project.mapLayers().values())


def _apply_datalayer_style(datalayer: DataLayer, layer) -> None:
    if not (datalayer.type == "RASTER" or datalayer.map_service_type == "COG"):
        return
    style_data = _first_style_data(datalayer)
    if not isinstance(style_data, dict):
        return

    map_type = style_data.get("map_type")
    if map_type not in {"RAMP", "VALUES"}:
        return

    items = _color_ramp_items(style_data)
    if not items:
        return

    color_ramp = QgsColorRampShader()
    color_ramp.setColorRampType(_color_ramp_type(map_type))
    color_ramp.setColorRampItemList(items)

    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(color_ramp)
    layer.setRenderer(QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, raster_shader))


def _color_ramp_type(map_type: str):
    if map_type == "VALUES":
        return QgsColorRampShader.Type.Exact
    return QgsColorRampShader.Type.Linear


def _first_style_data(datalayer: DataLayer):
    if not datalayer.styles:
        return None
    first_style = datalayer.styles[0]
    if not isinstance(first_style, dict):
        return None
    return first_style.get("data")


def _color_ramp_items(style_data: dict) -> list:
    items = []
    for entry in style_data.get("entries", []):
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        color = _qcolor(entry)
        if not isinstance(value, int | float) or color is None:
            continue
        label = entry.get("label")
        items.append(QgsColorRampShader.ColorRampItem(float(value), color, str(label or value)))

    no_data = style_data.get("no_data")
    if isinstance(no_data, dict):
        color = _qcolor(no_data)
        for value in no_data.get("values", []):
            if isinstance(value, int | float) and color is not None:
                label = no_data.get("label")
                items.append(QgsColorRampShader.ColorRampItem(float(value), color, str(label or value)))

    items.sort(key=lambda item: item.value)
    return items


def _qcolor(entry: dict) -> QColor | None:
    color_value = entry.get("color")
    if not isinstance(color_value, str):
        return None
    color = QColor(color_value)
    if not color.isValid():
        return None
    opacity = entry.get("opacity")
    if isinstance(opacity, int | float):
        color.setAlphaF(max(0.0, min(1.0, float(opacity))))
    return color
