from qgis.PyQt.QtGui import QColor

from planscape.processing import raster_style


def test_planscape_style_from_raster_layer_converts_linear_ramp(monkeypatch):
    class FakeType:
        Exact = "exact"
        Discrete = "discrete"
        Linear = "linear"

    class FakeColorRampShader:
        Type = FakeType

    class FakeRenderer:
        def shader(self):
            return FakeShader()

        def usesBands(self):
            return [1]

    class FakeShader:
        def rasterShaderFunction(self):
            return FakeShaderFunction()

    class FakeShaderFunction(FakeColorRampShader):
        def colorRampType(self):
            return FakeType.Linear

        def colorRampItemList(self):
            return [FakeItem(0, "low", QColor("#000000")), FakeItem(10, "high", QColor("#ffffff"))]

    class FakeItem:
        def __init__(self, value, label, color):
            self.value = value
            self.label = label
            self.color = color

    class FakeProvider:
        def sourceHasNoDataValue(self, band):
            return band == 1

        def sourceNoDataValue(self, band):
            del band
            return -9999

    class FakeLayer:
        def renderer(self):
            return FakeRenderer()

        def dataProvider(self):
            return FakeProvider()

    monkeypatch.setattr(raster_style, "QgsSingleBandPseudoColorRenderer", FakeRenderer)
    monkeypatch.setattr(raster_style, "QgsColorRampShader", FakeColorRampShader)

    style = raster_style.planscape_style_from_raster_layer(FakeLayer())

    assert style == {
        "map_type": "RAMP",
        "entries": [
            {"color": "#000000", "label": "low", "value": 0.0, "opacity": 1.0},
            {"color": "#ffffff", "label": "high", "value": 10.0, "opacity": 1.0},
        ],
        "no_data": {"color": None, "label": "No data", "values": [-9999], "opacity": 0},
    }


def test_planscape_style_from_raster_layer_skips_unsupported_renderer(monkeypatch):
    class FakeRenderer:
        pass

    class FakeLayer:
        def renderer(self):
            return FakeRenderer()

    monkeypatch.setattr(raster_style, "QgsSingleBandPseudoColorRenderer", type("OtherRenderer", (), {}))

    assert raster_style.planscape_style_from_raster_layer(FakeLayer()) is None
