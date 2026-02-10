from qgis.core import QgsProcessingProvider

from planscape.processing.import_raster import ImportRasterAlgorithm


class PlanscapeProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self) -> None:  # noqa: N802
        self.addAlgorithm(ImportRasterAlgorithm())

    def id(self) -> str:
        return "planscape"

    def name(self) -> str:
        return "Planscape"

    def longName(self) -> str:  # noqa: N802
        return self.name()
