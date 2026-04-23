from qgis.core import QgsProcessingProvider

from planscape.processing.import_raster import ImportRasterAlgorithm
from planscape.processing.import_vector import ImportVectorAlgorithm


class PlanscapeProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self) -> None:
        self.addAlgorithm(ImportRasterAlgorithm())
        self.addAlgorithm(ImportVectorAlgorithm())

    def id(self) -> str:
        return "planscape"

    def name(self) -> str:
        return "Planscape"

    def longName(self) -> str:
        return self.name()
