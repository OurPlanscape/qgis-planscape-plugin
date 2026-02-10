from qgis.core import QgsProcessingProvider

from planscape.processing.skeleton_algorithm import PlanscapeSkeletonAlgorithm


class PlanscapeProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self) -> None:  # noqa: N802
        self.addAlgorithm(PlanscapeSkeletonAlgorithm())

    def id(self) -> str:
        return "planscape"

    def name(self) -> str:
        return "Planscape"

    def longName(self) -> str:  # noqa: N802
        return self.name()

