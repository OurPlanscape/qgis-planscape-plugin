from typing import Any

from qgis.core import QgsProcessingAlgorithm, QgsProcessingContext, QgsProcessingFeedback


class PlanscapeSkeletonAlgorithm(QgsProcessingAlgorithm):
    def name(self) -> str:
        return "skeleton_algorithm"

    def displayName(self) -> str:  # noqa: N802
        return "Skeleton Algorithm"

    def group(self) -> str:
        return "Planscape"

    def groupId(self) -> str:  # noqa: N802
        return "planscape"

    def shortHelpString(self) -> str:  # noqa: N802
        return "Bare-bones processing algorithm skeleton."

    def createInstance(self) -> QgsProcessingAlgorithm:  # noqa: N802
        return PlanscapeSkeletonAlgorithm()

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:  # noqa: N802, ARG002
        # Intentionally empty: no parameters and no outputs.
        return

    def processAlgorithm(  # noqa: N802
        self,
        parameters: dict[str, Any],  # noqa: ARG002
        context: QgsProcessingContext,  # noqa: ARG002
        feedback: QgsProcessingFeedback,  # noqa: ARG002
    ) -> dict[str, Any]:
        # Intentionally empty: returns no outputs.
        return {}

