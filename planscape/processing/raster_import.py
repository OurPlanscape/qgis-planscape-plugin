from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from osgeo import gdal
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingUtils,
    QgsProject,
    QgsRasterBandStats,
    QgsRasterLayer,
)
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest

from planscape.api.datalayer import create_datalayer_request, update_datalayer_status_request
from planscape.api.exceptions import StyleAPIError, StylePayloadError
from planscape.api.style import create_style_request
from planscape.models.api.datalayer import CreateDataLayerRequest
from planscape.models.api.style import CreateStyleRequest
from planscape.processing.raster_style import planscape_style_from_raster_layer
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginNetworkException
from planscape.qgis_plugin_tools.tools.network import ENCODING

logger = logging.getLogger(__name__)
PLANSCAPE_RASTER_CRS = "EPSG:3857"
KNOWN_DATASET_MODULES = ("map", "forsys", "impacts", "climate_foresight")


@dataclass(frozen=True)
class RasterImportRequest:
    base_url: str
    authcfg_id: str
    layer: QgsRasterLayer
    name: str
    dataset: int
    workspace: int
    organization: int
    category: int | None = None
    metadata: dict[str, Any] | None = None
    dataset_modules: list[str] | None = None


@dataclass(frozen=True)
class RasterImportResult:
    datalayer_id: int
    datalayer_name: str
    style_id: int | None = None
    output_file: str | None = None


def import_raster_to_planscape(
    request: RasterImportRequest,
    context: QgsProcessingContext,
    feedback: QgsProcessingFeedback | None = None,
) -> RasterImportResult:
    feedback = feedback or QgsProcessingFeedback()
    input_file = _local_source_path(request.layer)
    metadata = metadata_with_modules(request.metadata or {}, request.dataset_modules or [])
    style_data = planscape_style_from_raster_layer(request.layer)

    feedback.pushInfo("Preparing raster for Planscape.")
    prepared_file = prepare_raster_for_planscape(input_file, request.layer, context, feedback)
    info = info_raster(prepared_file)

    feedback.pushInfo("Creating Planscape datalayer.")
    create_response = create_datalayer_request(
        request.base_url,
        request.authcfg_id,
        CreateDataLayerRequest(
            name=request.name,
            dataset=request.dataset,
            organization=request.organization,
            category=request.category,
            layer_info=info,
            metadata=metadata,
            original_name=Path(input_file).name,
        ),
    )
    if create_response.datalayer.id is None:
        message = "Planscape did not return a datalayer id."
        raise QgsProcessingException(message)

    if create_response.upload_to is None:
        message = "Planscape did not return an upload URL for the new datalayer."
        raise QgsProcessingException(message)

    feedback.pushInfo("Uploading raster to Planscape storage.")
    upload_file(create_response.upload_to.url, prepared_file)

    feedback.pushInfo("Marking datalayer READY.")
    update_datalayer_status_request(
        request.base_url,
        request.authcfg_id,
        create_response.datalayer.id,
        request.organization,
        "READY",
    )

    style_id = None
    if style_data is not None:
        try:
            feedback.pushInfo("Creating Planscape raster style from QGIS renderer.")
            style = create_style_request(
                request.base_url,
                request.authcfg_id,
                CreateStyleRequest(
                    name=f"{request.name} Style",
                    data=style_data,
                    organization=request.organization,
                    datalayers=[int(create_response.datalayer.id)],
                ),
            )
            if isinstance(style.id, int):
                style_id = style.id
        except (StyleAPIError, StylePayloadError) as exc:
            logger.warning("Failed to create raster style: %s", exc)
            feedback.reportError(f"Failed to create raster style: {exc}", fatalError=False)

    return RasterImportResult(
        datalayer_id=int(create_response.datalayer.id),
        datalayer_name=create_response.datalayer.name,
        style_id=style_id,
        output_file=prepared_file,
    )


def prepare_raster_for_planscape(
    input_file: str,
    layer: QgsRasterLayer,
    context: QgsProcessingContext,
    feedback: QgsProcessingFeedback,
) -> str:
    import processing

    if not layer.crs().isValid():
        message = "Cannot import raster without CRS information."
        raise QgsProcessingException(message)

    source = input_file
    if layer.crs().authid() != PLANSCAPE_RASTER_CRS:
        feedback.pushInfo(f"Reprojecting raster to {PLANSCAPE_RASTER_CRS}.")
        warped_output = _temporary_tif(input_file, "warped")
        result = processing.run(
            "gdal:warpreproject",
            {
                "INPUT": source,
                "SOURCE_CRS": None,
                "TARGET_CRS": PLANSCAPE_RASTER_CRS,
                "RESAMPLING": 0,
                "NODATA": None,
                "TARGET_RESOLUTION": None,
                "OPTIONS": "",
                "DATA_TYPE": 0,
                "TARGET_EXTENT": None,
                "TARGET_EXTENT_CRS": None,
                "MULTITHREADING": True,
                "EXTRA": "",
                "OUTPUT": warped_output,
            },
            context=context,
            feedback=feedback,
        )
        source = result["OUTPUT"]

    feedback.pushInfo("Converting raster to Cloud Optimized GeoTIFF.")
    cog_output = _temporary_tif(input_file, "cog")
    result = processing.run(
        "gdal:translate",
        {
            "INPUT": source,
            "TARGET_CRS": None,
            "NODATA": None,
            "COPY_SUBDATASETS": False,
            "OPTIONS": "COMPRESS=DEFLATE|BIGTIFF=IF_SAFER",
            "EXTRA": "-of COG",
            "DATA_TYPE": 0,
            "OUTPUT": cog_output,
        },
        context=context,
        feedback=feedback,
    )
    return str(result["OUTPUT"])


def info_raster(input_file: str) -> dict[str, Any]:
    layer = _prepared_raster_layer(input_file)
    dataset = gdal.Open(input_file, gdal.GA_ReadOnly)
    if dataset is None:
        message = "Prepared raster could not be read by GDAL."
        raise QgsProcessingException(message)

    provider = layer.dataProvider()
    extent = layer.extent()
    transform = dataset.GetGeoTransform(can_return_null=True)
    if transform is None:
        transform = (
            extent.xMinimum(),
            layer.rasterUnitsPerPixelX(),
            0,
            extent.yMaximum(),
            0,
            -layer.rasterUnitsPerPixelY(),
        )

    band = dataset.GetRasterBand(1) if dataset.RasterCount else None
    nodata = band.GetNoDataValue() if band is not None else None
    image_structure = dataset.GetMetadata("IMAGE_STRUCTURE") or {}
    block_size = band.GetBlockSize() if band is not None else [None, None]

    return {
        "crs": layer.crs().authid(),
        "res": [abs(transform[1]), abs(transform[5])],
        "count": layer.bandCount(),
        "dtype": _dtype(dataset),
        "shape": [layer.height(), layer.width()],
        "stats": [_band_stats(provider, band_index) for band_index in range(1, layer.bandCount() + 1)],
        "tiled": _is_tiled(dataset, block_size),
        "units": [_unit(dataset, band_index) for band_index in range(1, layer.bandCount() + 1)],
        "width": layer.width(),
        "bounds": [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()],
        "driver": dataset.GetDriver().ShortName if dataset.GetDriver() else None,
        "height": layer.height(),
        "lnglat": _lnglat(layer),
        "nodata": nodata,
        "indexes": list(range(1, layer.bandCount() + 1)),
        "checksum": [_checksum(dataset, band_index) for band_index in range(1, layer.bandCount() + 1)],
        "compress": _metadata_value_lower(image_structure, "COMPRESSION"),
        "transform": [
            transform[1],
            transform[2],
            transform[0],
            transform[4],
            transform[5],
            transform[3],
            0,
            0,
            1,
        ],
        "blockxsize": block_size[0],
        "blockysize": block_size[1],
        "interleave": _metadata_value_lower(image_structure, "INTERLEAVE"),
        "mask_flags": [_mask_flags(dataset, band_index) for band_index in range(1, layer.bandCount() + 1)],
        "colorinterp": [_color_interpretation(dataset, band_index) for band_index in range(1, layer.bandCount() + 1)],
        "descriptions": [
            _empty_string_to_none(dataset.GetRasterBand(band_index).GetDescription())
            for band_index in range(1, layer.bandCount() + 1)
        ],
    }


def _band_stats(provider, band_index: int) -> dict[str, float | int | None]:
    stats = provider.bandStatistics(
        band_index,
        QgsRasterBandStats.Stats.Min
        | QgsRasterBandStats.Stats.Max
        | QgsRasterBandStats.Stats.Mean
        | QgsRasterBandStats.Stats.StdDev,
    )
    return {"max": stats.maximumValue, "min": stats.minimumValue, "std": stats.stdDev, "mean": stats.mean}


def _checksum(dataset, band_index: int) -> int | None:
    band = dataset.GetRasterBand(band_index)
    if band is None:
        return None
    return band.Checksum()


def _color_interpretation(dataset, band_index: int) -> str | None:
    band = dataset.GetRasterBand(band_index)
    if band is None:
        return None
    name = gdal.GetColorInterpretationName(band.GetColorInterpretation())
    if not name:
        return None
    return name.lower()


def _dtype(dataset) -> str | None:
    band = dataset.GetRasterBand(1) if dataset.RasterCount else None
    if band is None:
        return None
    return gdal.GetDataTypeName(band.DataType).lower()


def _empty_string_to_none(value) -> Any:
    return value if value != "" else None


def _is_tiled(dataset, block_size: list[int | None]) -> bool:
    return bool(
        block_size[0] and block_size[1] and block_size[0] < dataset.RasterXSize and block_size[1] < dataset.RasterYSize
    )


def _lnglat(layer: QgsRasterLayer) -> list[float] | None:
    if not layer.crs().isValid():
        return None
    center = layer.extent().center()
    transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
    point = transform.transform(center)
    return [point.x(), point.y()]


def _mask_flags(dataset, band_index: int) -> list[str]:
    band = dataset.GetRasterBand(band_index)
    if band is None:
        return []
    if band.GetNoDataValue() is not None:
        return ["nodata"]
    return ["all_valid"]


def _metadata_value_lower(metadata: dict[str, str], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    return value.lower()


def _unit(dataset, band_index: int) -> str | None:
    band = dataset.GetRasterBand(band_index)
    if band is None:
        return None
    return _empty_string_to_none(band.GetUnitType())


def _prepared_raster_layer(input_file: str) -> QgsRasterLayer:
    layer = QgsRasterLayer(input_file, Path(input_file).stem, "gdal")
    if not layer.isValid():
        message = "Prepared raster could not be read by QGIS."
        raise QgsProcessingException(message)
    return layer


def upload_file(url: str, input_file: str) -> None:
    from qgis.core import QgsBlockingNetworkRequest

    logger.info("[API] PUT:%s", url)
    request = QNetworkRequest(QUrl(url))
    request.setRawHeader(b"Content-Type", b"image/tiff")
    request.setRawHeader(b"User-Agent", bytes("QGIS Planscape", ENCODING))
    blocking_request = QgsBlockingNetworkRequest()
    blocking_request.put(request, Path(input_file).read_bytes())
    reply = blocking_request.reply()
    if reply.error() != QNetworkReply.NetworkError.NoError:
        message = bytes(reply.content()).decode(ENCODING) if bytes(reply.content()) else None
        logger.info("[API] FAILED:PUT:%s:%s", url, message or reply.errorString())
        raise QgsPluginNetworkException(message=message, error=reply.error(), bar_msg=reply.errorString())
    logger.info("[API] SUCCESS:PUT:%s", url)


def parse_metadata(value: str) -> dict[str, Any]:
    if not value.strip():
        return {}
    try:
        metadata = json.loads(value)
    except json.JSONDecodeError as exc:
        message = "Metadata must be valid JSON."
        raise QgsProcessingException(message) from exc
    if not isinstance(metadata, dict):
        message = "Metadata must be a JSON object."
        raise QgsProcessingException(message)
    return metadata


def metadata_with_modules(metadata: dict[str, Any], dataset_modules: list[str]) -> dict[str, Any]:
    enabled_modules = {module.strip() for module in dataset_modules if module.strip()}
    module_names = (*KNOWN_DATASET_MODULES, *sorted(enabled_modules - set(KNOWN_DATASET_MODULES)))
    modules = metadata.get("modules")
    if not isinstance(modules, dict):
        modules = {}

    updated_metadata = dict(metadata)
    updated_modules = dict(modules)
    for module in module_names:
        existing = updated_modules.get(module)
        module_metadata = dict(existing) if isinstance(existing, dict) else {}
        module_metadata["enabled"] = module in enabled_modules
        updated_modules[module] = module_metadata

    updated_metadata["modules"] = updated_modules
    return updated_metadata


def _local_source_path(layer: QgsRasterLayer) -> str:
    source = layer.source().split("|")[0]
    if not source or source.startswith(("/vsis3/", "/vsigs/", "s3://", "gs://", "http://", "https://")):
        message = "Only local raster files are supported for import."
        raise QgsProcessingException(message)
    if not Path(source).exists():
        message = f"Raster source does not exist: {source}"
        raise QgsProcessingException(message)
    return source


def _temporary_tif(input_file: str, suffix: str) -> str:
    stem = Path(input_file).stem
    return QgsProcessingUtils.generateTempFilename(f"{stem}_{suffix}.tif")
