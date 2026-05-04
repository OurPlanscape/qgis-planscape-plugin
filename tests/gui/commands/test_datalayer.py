from planscape.gui.commands import datalayer
from planscape.models.api.datalayer import DataLayerUrlsResponse
from planscape.models.domain import DataLayer


def test_add_datalayer_to_project_adds_raster_cog(monkeypatch):
    added = []
    created = {}

    class FakeLayer:
        def isValid(self):
            return True

    class FakeProject:
        def mapLayers(self):
            return {}

        def addMapLayer(self, layer):
            added.append(layer)

    def fake_raster_layer(url, name, provider):
        created["raster"] = {"url": url, "name": name, "provider": provider}
        return FakeLayer()

    monkeypatch.setattr(datalayer.auth, "get_base_url", lambda environment: f"https://{environment}.example")
    monkeypatch.setattr(datalayer.auth, "get_environment", lambda: "catalog")
    monkeypatch.setattr(datalayer.auth, "ensure_authenticated", lambda: "authcfg-id")

    def fake_retrieve_urls(base_url, authcfg_id, datalayer_id):
        del base_url, authcfg_id, datalayer_id
        return DataLayerUrlsResponse("https://example.test/cog.tif")

    monkeypatch.setattr(
        datalayer,
        "retrieve_datalayer_urls_request",
        fake_retrieve_urls,
    )
    monkeypatch.setattr(datalayer, "QgsRasterLayer", fake_raster_layer)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(DataLayer(id=10, name="Smoke", type="RASTER", status="READY"))

    assert created["raster"] == {"url": "https://example.test/cog.tif", "name": "[PS] Smoke", "provider": "gdal"}
    assert len(added) == 1


def test_add_datalayer_to_project_adds_vector_tile_layer(monkeypatch):
    added = []
    created = {}

    class FakeLayer:
        def isValid(self):
            return True

    class FakeProject:
        def mapLayers(self):
            return {}

        def addMapLayer(self, layer):
            added.append(layer)

    def fake_vector_tile_layer(uri, name):
        created["vector_tile"] = {"uri": uri, "name": name}
        return FakeLayer()

    monkeypatch.setattr(datalayer.auth, "get_base_url", lambda environment: f"https://{environment}.example")
    monkeypatch.setattr(datalayer.auth, "get_environment", lambda: "catalog")
    monkeypatch.setattr(datalayer.auth, "ensure_authenticated", lambda: "authcfg-id")

    def fake_retrieve_urls(base_url, authcfg_id, datalayer_id):
        del base_url, authcfg_id, datalayer_id
        return DataLayerUrlsResponse("https://example.test/tiles/dynamic/{z}/{x}/{y}?layer=10")

    monkeypatch.setattr(
        datalayer,
        "retrieve_datalayer_urls_request",
        fake_retrieve_urls,
    )
    monkeypatch.setattr(datalayer, "QgsVectorTileLayer", fake_vector_tile_layer)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(DataLayer(id=10, name="Parcels", type="VECTOR", status="READY"))

    assert created["vector_tile"] == {
        "uri": "type=xyz&url=https://example.test/tiles/dynamic/{z}/{x}/{y}?layer=10",
        "name": "[PS] Parcels",
    }
    assert len(added) == 1


def test_add_datalayer_to_project_skips_existing_toc_layer(monkeypatch):
    calls = []

    class ExistingLayer:
        def name(self):
            return "[PS] Smoke"

    class FakeProject:
        def mapLayers(self):
            return {"existing": ExistingLayer()}

        def addMapLayer(self, layer):
            calls.append(("add", layer))

    def fake_retrieve_urls(base_url, authcfg_id, datalayer_id):
        calls.append((base_url, authcfg_id, datalayer_id))
        return DataLayerUrlsResponse("https://example.test/cog.tif")

    monkeypatch.setattr(datalayer, "retrieve_datalayer_urls_request", fake_retrieve_urls)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(DataLayer(id=10, name="Smoke", type="RASTER", status="READY"))

    assert calls == []


def test_add_datalayer_to_project_uses_existing_map_url(monkeypatch):
    added = []
    created = {}

    class FakeLayer:
        def isValid(self):
            return True

    class FakeProject:
        def mapLayers(self):
            return {}

        def addMapLayer(self, layer):
            added.append(layer)

    def fail_retrieve_urls(base_url, authcfg_id, datalayer_id):
        del base_url, authcfg_id, datalayer_id
        message = "URL endpoint should not be called when map_url is present"
        raise AssertionError(message)

    def fake_raster_layer(url, name, provider):
        created["raster"] = {"url": url, "name": name, "provider": provider}
        return FakeLayer()

    monkeypatch.setattr(datalayer, "retrieve_datalayer_urls_request", fail_retrieve_urls)
    monkeypatch.setattr(datalayer, "QgsRasterLayer", fake_raster_layer)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(
        DataLayer(
            id=10,
            name="Smoke",
            type="RASTER",
            status="READY",
            map_url="https://example.test/from-browse.tif",
        )
    )

    assert created["raster"] == {
        "url": "https://example.test/from-browse.tif",
        "name": "[PS] Smoke",
        "provider": "gdal",
    }
    assert len(added) == 1


def test_add_datalayer_to_project_skips_invalid_layer(monkeypatch):
    added = []

    class FakeLayer:
        def isValid(self):
            return False

    class FakeProject:
        def mapLayers(self):
            return {}

        def addMapLayer(self, layer):
            added.append(layer)

    monkeypatch.setattr(datalayer.auth, "get_base_url", lambda environment: f"https://{environment}.example")
    monkeypatch.setattr(datalayer.auth, "get_environment", lambda: "catalog")
    monkeypatch.setattr(datalayer.auth, "ensure_authenticated", lambda: "authcfg-id")

    def fake_retrieve_urls(base_url, authcfg_id, datalayer_id):
        del base_url, authcfg_id, datalayer_id
        return DataLayerUrlsResponse("https://example.test/cog.tif")

    def fake_raster_layer(url, name, provider):
        del url, name, provider
        return FakeLayer()

    monkeypatch.setattr(
        datalayer,
        "retrieve_datalayer_urls_request",
        fake_retrieve_urls,
    )
    monkeypatch.setattr(datalayer, "QgsRasterLayer", fake_raster_layer)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(DataLayer(id=10, name="Smoke", type="RASTER", status="READY"))

    assert added == []


def test_add_datalayer_to_project_applies_raster_ramp_style(monkeypatch):
    rendered = {}

    class FakeLayer:
        def isValid(self):
            return True

        def dataProvider(self):
            return "provider"

        def setRenderer(self, renderer):
            rendered["renderer"] = renderer

    class FakeProject:
        def mapLayers(self):
            return {}

        def addMapLayer(self, layer):
            del layer

    class FakeColorRampShader:
        class Type:
            Linear = "linear"
            Exact = "exact"

        class ColorRampItem:
            def __init__(self, value, color, label):
                self.value = value
                self.color = color
                self.label = label

        def setColorRampType(self, ramp_type):
            rendered["ramp_type"] = ramp_type

        def setColorRampItemList(self, items):
            rendered["items"] = items

    class FakeRasterShader:
        def setRasterShaderFunction(self, function):
            rendered["shader_function"] = function

    class FakeRenderer:
        def __init__(self, provider, band, shader):
            rendered["provider"] = provider
            rendered["band"] = band
            rendered["shader"] = shader

    monkeypatch.setattr(datalayer.auth, "get_base_url", lambda environment: f"https://{environment}.example")
    monkeypatch.setattr(datalayer.auth, "get_environment", lambda: "catalog")
    monkeypatch.setattr(datalayer.auth, "ensure_authenticated", lambda: "authcfg-id")

    def fake_retrieve_urls(base_url, authcfg_id, datalayer_id):
        del base_url, authcfg_id, datalayer_id
        return DataLayerUrlsResponse("https://example.test/cog.tif")

    def fake_raster_layer(url, name, provider):
        del url, name, provider
        return FakeLayer()

    monkeypatch.setattr(datalayer, "retrieve_datalayer_urls_request", fake_retrieve_urls)
    monkeypatch.setattr(datalayer, "QgsRasterLayer", fake_raster_layer)
    monkeypatch.setattr(datalayer, "QgsColorRampShader", FakeColorRampShader)
    monkeypatch.setattr(datalayer, "QgsRasterShader", FakeRasterShader)
    monkeypatch.setattr(datalayer, "QgsSingleBandPseudoColorRenderer", FakeRenderer)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(
        DataLayer(
            id=10,
            name="Smoke",
            type="RASTER",
            status="READY",
            styles=[
                {
                    "data": {
                        "map_type": "RAMP",
                        "entries": [
                            {"color": "#FBEFD6", "label": "low", "value": 0.02, "opacity": 1},
                            {"color": "#F18D13", "label": "high", "value": 1, "opacity": 0.5},
                        ],
                    }
                }
            ],
        )
    )

    assert rendered["ramp_type"] == "linear"
    assert [(item.value, item.label) for item in rendered["items"]] == [(0.02, "low"), (1.0, "high")]
    assert rendered["provider"] == "provider"
    assert rendered["band"] == 1
    assert "renderer" in rendered


def test_add_datalayer_to_project_applies_raster_values_style(monkeypatch):
    rendered = {}

    class FakeLayer:
        def isValid(self):
            return True

        def dataProvider(self):
            return "provider"

        def setRenderer(self, renderer):
            rendered["renderer"] = renderer

    class FakeProject:
        def mapLayers(self):
            return {}

        def addMapLayer(self, layer):
            del layer

    class FakeColorRampShader:
        class Type:
            Linear = "linear"
            Exact = "exact"

        class ColorRampItem:
            def __init__(self, value, color, label):
                self.value = value
                self.color = color
                self.label = label

        def setColorRampType(self, ramp_type):
            rendered["ramp_type"] = ramp_type

        def setColorRampItemList(self, items):
            rendered["items"] = items

    class FakeRasterShader:
        def setRasterShaderFunction(self, function):
            rendered["shader_function"] = function

    class FakeRenderer:
        def __init__(self, provider, band, shader):
            rendered["provider"] = provider
            rendered["band"] = band
            rendered["shader"] = shader

    monkeypatch.setattr(datalayer.auth, "get_base_url", lambda environment: f"https://{environment}.example")
    monkeypatch.setattr(datalayer.auth, "get_environment", lambda: "catalog")
    monkeypatch.setattr(datalayer.auth, "ensure_authenticated", lambda: "authcfg-id")

    def fake_retrieve_urls(base_url, authcfg_id, datalayer_id):
        del base_url, authcfg_id, datalayer_id
        return DataLayerUrlsResponse("https://example.test/cog.tif")

    def fake_raster_layer(url, name, provider):
        del url, name, provider
        return FakeLayer()

    monkeypatch.setattr(datalayer, "retrieve_datalayer_urls_request", fake_retrieve_urls)
    monkeypatch.setattr(datalayer, "QgsRasterLayer", fake_raster_layer)
    monkeypatch.setattr(datalayer, "QgsColorRampShader", FakeColorRampShader)
    monkeypatch.setattr(datalayer, "QgsRasterShader", FakeRasterShader)
    monkeypatch.setattr(datalayer, "QgsSingleBandPseudoColorRenderer", FakeRenderer)
    monkeypatch.setattr(datalayer.QgsProject, "instance", lambda: FakeProject())

    datalayer.add_datalayer_to_project(
        DataLayer(
            id=10,
            name="Critical Habitat",
            type="RASTER",
            status="READY",
            styles=[
                {
                    "data": {
                        "map_type": "VALUES",
                        "entries": [{"color": "#30123b", "label": "Critical Habitat", "value": 1, "opacity": 1}],
                        "no_data": {"color": None, "label": None, "values": [0], "opacity": 0},
                    }
                }
            ],
        )
    )

    assert rendered["ramp_type"] == "exact"
    assert [(item.value, item.label) for item in rendered["items"]] == [(1.0, "Critical Habitat")]
    assert rendered["provider"] == "provider"
    assert rendered["band"] == 1
    assert "renderer" in rendered
