from __future__ import annotations

from typing import Any

from qgis.core import QgsColorRampShader, QgsRasterLayer, QgsSingleBandPseudoColorRenderer
from qgis.PyQt.QtGui import QColor


def planscape_style_from_raster_layer(layer: QgsRasterLayer) -> dict[str, Any] | None:
    renderer = layer.renderer()
    if not isinstance(renderer, QgsSingleBandPseudoColorRenderer):
        return None

    shader = renderer.shader()
    if shader is None:
        return None
    shader_function = shader.rasterShaderFunction()
    if not isinstance(shader_function, QgsColorRampShader):
        return None

    map_type = _map_type(shader_function.colorRampType())
    if map_type is None:
        return None

    entries = [_style_entry(item) for item in shader_function.colorRampItemList()]
    entries = [entry for entry in entries if entry is not None]
    if not entries:
        return None

    style: dict[str, Any] = {"map_type": map_type, "entries": entries}
    no_data = _no_data(layer, renderer.usesBands()[0] if renderer.usesBands() else 1)
    if no_data is not None:
        style["no_data"] = no_data
    return style


def _map_type(ramp_type) -> str | None:
    if ramp_type == QgsColorRampShader.Type.Exact:
        return "VALUES"
    if ramp_type == QgsColorRampShader.Type.Discrete:
        return "VALUES"
    if ramp_type == QgsColorRampShader.Type.Linear:
        return "RAMP"
    return None


def _style_entry(item) -> dict[str, Any] | None:
    color = getattr(item, "color", None)
    value = getattr(item, "value", None)
    if not isinstance(color, QColor) or not isinstance(value, int | float):
        return None
    label = getattr(item, "label", None) or str(value)
    return {
        "color": color.name(QColor.NameFormat.HexRgb),
        "label": str(label),
        "value": float(value),
        "opacity": color.alphaF(),
    }


def _no_data(layer: QgsRasterLayer, band: int) -> dict[str, Any] | None:
    provider = layer.dataProvider()
    if provider is None or not provider.sourceHasNoDataValue(band):
        return None
    value = provider.sourceNoDataValue(band)
    if not isinstance(value, int | float):
        return None
    return {"color": None, "label": "No data", "values": [value], "opacity": 0}
