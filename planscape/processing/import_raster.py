from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from planscape.auth import ensure_authenticated


class ImportRasterAlgorithm(QgsProcessingAlgorithm):
    def name(self) -> str:
        return "import_raster"

    def displayName(self) -> str:
        return "Import Raster"

    def group(self) -> str:
        return "Import"

    def groupId(self) -> str:
        return "import"

    def shortHelpString(self) -> str:
        return "Imports one or more rasters into Planscape"

    def createInstance(self) -> QgsProcessingAlgorithm:
        return ImportRasterAlgorithm()

    def initAlgorithm(self, configuration: Optional[dict[str, Any]] = None) -> None:  # noqa: ARG002
        # Intentionally empty: no parameters and no outputs.
        return

    def processAlgorithm(
        self,
        parameters: dict[str, Any],  # noqa: ARG002
        context: QgsProcessingContext,  # noqa: ARG002
        feedback: Optional[QgsProcessingFeedback],  # noqa: ARG002
    ) -> dict[str, Any]:
        ensure_authenticated()
        # Intentionally empty: returns no outputs.
        return {}
