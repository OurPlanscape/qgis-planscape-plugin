import pytest
from osgeo import gdal, osr
from qgis.core import QgsProcessingException

from planscape.api.exceptions import StylePayloadError
from planscape.models.api.datalayer import CreateDataLayerResponse, DataLayerUploadTarget
from planscape.models.domain import DataLayer, Style
from planscape.processing import raster_import
from planscape.processing.raster_import import RasterImportRequest


class FakeFeedback:
    def pushInfo(self, message):
        del message

    def reportError(self, message, **kwargs):
        del message, kwargs


class FakeLayer:
    pass


def test_import_raster_uploads_before_marking_ready_and_then_creates_style(monkeypatch):
    calls = []

    def fake_local_source_path(layer):
        del layer
        return "/tmp/input.tif"

    def fake_style(layer):
        del layer
        return {"map_type": "RAMP"}

    def fake_prepare_raster_for_planscape(input_file, layer, context, feedback):
        del input_file, layer, context, feedback
        return "/tmp/prepared.tif"

    def fake_info_raster(input_file):
        del input_file
        return {"crs": "EPSG:3857"}

    monkeypatch.setattr(raster_import, "_local_source_path", fake_local_source_path)
    monkeypatch.setattr(raster_import, "planscape_style_from_raster_layer", fake_style)
    monkeypatch.setattr(raster_import, "prepare_raster_for_planscape", fake_prepare_raster_for_planscape)
    monkeypatch.setattr(raster_import, "info_raster", fake_info_raster)

    def fake_create_datalayer_request(base_url, authcfg_id, request):
        calls.append(("create", base_url, authcfg_id, request.layer_info, request.metadata))
        return CreateDataLayerResponse(
            datalayer=DataLayer(id=20, name="Smoke"),
            upload_to=DataLayerUploadTarget(url="https://storage.example/upload"),
        )

    def fake_upload_file(url, input_file):
        calls.append(("upload", url, input_file))

    def fake_update_status(base_url, authcfg_id, datalayer_id, organization, status):
        calls.append(("ready", base_url, authcfg_id, datalayer_id, organization, status))
        return {"status": status}

    def fake_create_style(base_url, authcfg_id, request):
        calls.append(("style", base_url, authcfg_id, request.datalayers))
        return Style(id=30, name="Smoke Style")

    monkeypatch.setattr(raster_import, "create_datalayer_request", fake_create_datalayer_request)
    monkeypatch.setattr(raster_import, "upload_file", fake_upload_file)
    monkeypatch.setattr(raster_import, "update_datalayer_status_request", fake_update_status)
    monkeypatch.setattr(raster_import, "create_style_request", fake_create_style)

    result = raster_import.import_raster_to_planscape(
        RasterImportRequest(
            base_url="https://planscape.example",
            authcfg_id="authcfg-id",
            layer=FakeLayer(),
            name="Smoke",
            dataset=10,
            workspace=5,
            organization=3,
            dataset_modules=["map", "climate_foresight"],
        ),
        context=None,
        feedback=FakeFeedback(),
    )

    assert [call[0] for call in calls] == ["create", "upload", "ready", "style"]
    assert calls[0][3] == {"crs": "EPSG:3857"}
    assert calls[0][4] == {
        "modules": {
            "map": {"enabled": True},
            "forsys": {"enabled": False},
            "impacts": {"enabled": False},
            "climate_foresight": {"enabled": True},
        }
    }
    assert calls[1] == ("upload", "https://storage.example/upload", "/tmp/prepared.tif")
    assert calls[2] == ("ready", "https://planscape.example", "authcfg-id", 20, 3, "READY")
    assert calls[3] == ("style", "https://planscape.example", "authcfg-id", [20])
    assert result.datalayer_id == 20
    assert result.style_id == 30


def test_import_raster_requires_upload_url_before_marking_ready(monkeypatch):
    ready_called = {"value": False}

    def fake_local_source_path(layer):
        del layer
        return "/tmp/input.tif"

    def fake_style(layer):
        del layer

    def fake_prepare_raster_for_planscape(input_file, layer, context, feedback):
        del input_file, layer, context, feedback
        return "/tmp/prepared.tif"

    def fake_info_raster(input_file):
        del input_file
        return {"crs": "EPSG:3857"}

    def fake_create_datalayer_request(base_url, authcfg_id, request):
        del base_url, authcfg_id, request
        return CreateDataLayerResponse(datalayer=DataLayer(id=20, name="Smoke"), upload_to=None)

    monkeypatch.setattr(raster_import, "_local_source_path", fake_local_source_path)
    monkeypatch.setattr(raster_import, "planscape_style_from_raster_layer", fake_style)
    monkeypatch.setattr(raster_import, "prepare_raster_for_planscape", fake_prepare_raster_for_planscape)
    monkeypatch.setattr(raster_import, "info_raster", fake_info_raster)
    monkeypatch.setattr(raster_import, "create_datalayer_request", fake_create_datalayer_request)

    def fake_update_status(*args):
        del args
        ready_called["value"] = True
        return {}

    monkeypatch.setattr(raster_import, "update_datalayer_status_request", fake_update_status)

    with pytest.raises(QgsProcessingException, match="upload URL"):
        raster_import.import_raster_to_planscape(
            RasterImportRequest(
                base_url="https://planscape.example",
                authcfg_id="authcfg-id",
                layer=FakeLayer(),
                name="Smoke",
                dataset=10,
                workspace=5,
                organization=3,
            ),
            context=None,
            feedback=FakeFeedback(),
        )

    assert ready_called["value"] is False


def test_metadata_with_modules_preserves_existing_module_metadata():
    metadata = {"modules": {"impacts": {"variable": "fire"}}, "source": "qgis"}

    result = raster_import.metadata_with_modules(metadata, ["map", "impacts"])

    assert result == {
        "source": "qgis",
        "modules": {
            "map": {"enabled": True},
            "forsys": {"enabled": False},
            "impacts": {"variable": "fire", "enabled": True},
            "climate_foresight": {"enabled": False},
        },
    }


def test_import_raster_does_not_fail_when_style_response_is_invalid(monkeypatch):
    def fake_local_source_path(layer):
        del layer
        return "/tmp/input.tif"

    def fake_style(layer):
        del layer
        return {"map_type": "RAMP"}

    def fake_prepare_raster_for_planscape(input_file, layer, context, feedback):
        del input_file, layer, context, feedback
        return "/tmp/prepared.tif"

    def fake_info_raster(input_file):
        del input_file
        return {"crs": "EPSG:3857"}

    def fake_create_datalayer_request(base_url, authcfg_id, request):
        del base_url, authcfg_id, request
        return CreateDataLayerResponse(
            datalayer=DataLayer(id=20, name="Smoke"),
            upload_to=DataLayerUploadTarget(url="https://storage.example/upload"),
        )

    def fake_upload_file(url, input_file):
        del url, input_file

    def fake_update_status(base_url, authcfg_id, datalayer_id, organization, status):
        del base_url, authcfg_id, datalayer_id, organization, status
        return {}

    def fake_create_style(base_url, authcfg_id, request):
        del base_url, authcfg_id, request
        message = "id must be an integer."
        raise StylePayloadError(message)

    monkeypatch.setattr(raster_import, "_local_source_path", fake_local_source_path)
    monkeypatch.setattr(raster_import, "planscape_style_from_raster_layer", fake_style)
    monkeypatch.setattr(raster_import, "prepare_raster_for_planscape", fake_prepare_raster_for_planscape)
    monkeypatch.setattr(raster_import, "info_raster", fake_info_raster)
    monkeypatch.setattr(raster_import, "create_datalayer_request", fake_create_datalayer_request)
    monkeypatch.setattr(raster_import, "upload_file", fake_upload_file)
    monkeypatch.setattr(raster_import, "update_datalayer_status_request", fake_update_status)
    monkeypatch.setattr(raster_import, "create_style_request", fake_create_style)

    result = raster_import.import_raster_to_planscape(
        RasterImportRequest(
            base_url="https://planscape.example",
            authcfg_id="authcfg-id",
            layer=FakeLayer(),
            name="Smoke",
            dataset=10,
            workspace=5,
            organization=3,
        ),
        context=None,
        feedback=FakeFeedback(),
    )

    assert result.datalayer_id == 20
    assert result.style_id is None


def test_info_raster_returns_rasterio_style_shape(tmp_path):
    raster_path = tmp_path / "info.tif"
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        str(raster_path),
        4,
        3,
        1,
        gdal.GDT_Int16,
        options=["TILED=YES", "BLOCKXSIZE=16", "BLOCKYSIZE=16", "COMPRESS=DEFLATE"],
    )
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(3857)
    dataset.SetProjection(spatial_ref.ExportToWkt())
    dataset.SetGeoTransform((100, 30, 0, 200, 0, -30))
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(-999)
    band.Fill(5)
    band.FlushCache()
    dataset.FlushCache()
    dataset = None

    info = raster_import.info_raster(str(raster_path))

    assert info["crs"] == "EPSG:3857"
    assert info["res"] == [30, 30]
    assert info["count"] == 1
    assert info["dtype"] == "int16"
    assert info["shape"] == [3, 4]
    assert info["width"] == 4
    assert info["height"] == 3
    assert info["bounds"] == [100.0, 110.0, 220.0, 200.0]
    assert info["driver"] == "GTiff"
    assert info["nodata"] == -999
    assert info["indexes"] == [1]
    assert info["compress"] == "deflate"
    assert info["transform"] == [30.0, 0.0, 100.0, 0.0, -30.0, 200.0, 0, 0, 1]
    assert info["blockxsize"] == 16
    assert info["blockysize"] == 16
    assert info["interleave"] == "band"
    assert info["mask_flags"] == [["nodata"]]
    assert info["colorinterp"] == ["gray"]
    assert info["descriptions"] == [None]
    assert info["units"] == [None]
    assert isinstance(info["checksum"][0], int)
    assert info["stats"][0]["min"] == 5
    assert info["stats"][0]["max"] == 5
    assert len(info["lnglat"]) == 2
