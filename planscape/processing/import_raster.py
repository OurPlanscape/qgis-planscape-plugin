from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
)

from planscape import auth
from planscape.auth import ensure_authenticated
from planscape.processing.raster_import import RasterImportRequest, import_raster_to_planscape, parse_metadata

INPUT = "INPUT"
NAME = "NAME"
DATASET = "DATASET"
ORGANIZATION = "ORGANIZATION"
CATEGORY = "CATEGORY"
METADATA = "METADATA"
DATALAYER_ID = "DATALAYER_ID"
DATALAYER_NAME = "DATALAYER_NAME"
STYLE_ID = "STYLE_ID"
OUTPUT_FILE = "OUTPUT_FILE"


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
        self.addParameter(QgsProcessingParameterRasterLayer(INPUT, "Raster layer"))
        self.addParameter(QgsProcessingParameterString(NAME, "Datalayer name"))
        self.addParameter(
            QgsProcessingParameterNumber(DATASET, "Dataset ID", QgsProcessingParameterNumber.Type.Integer)
        )
        self.addParameter(
            QgsProcessingParameterNumber(ORGANIZATION, "Organization ID", QgsProcessingParameterNumber.Type.Integer)
        )
        category = QgsProcessingParameterNumber(
            CATEGORY,
            "Category ID",
            QgsProcessingParameterNumber.Type.Integer,
            optional=True,
        )
        category.setFlags(category.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(category)
        metadata = QgsProcessingParameterString(METADATA, "Metadata JSON", optional=True, multiLine=True)
        metadata.setFlags(metadata.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(metadata)

        self.addOutput(QgsProcessingOutputNumber(DATALAYER_ID, "Datalayer ID"))
        self.addOutput(QgsProcessingOutputString(DATALAYER_NAME, "Datalayer name"))
        self.addOutput(QgsProcessingOutputNumber(STYLE_ID, "Style ID"))
        self.addOutput(QgsProcessingOutputString(OUTPUT_FILE, "Prepared COG"))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: Optional[QgsProcessingFeedback],
    ) -> dict[str, Any]:
        authcfg_id = ensure_authenticated()
        if not parameters:
            return {}
        layer = self.parameterAsRasterLayer(parameters, INPUT, context)
        if layer is None or not layer.isValid():
            message = "A valid local raster layer is required."
            raise QgsProcessingException(message)

        category = _optional_int_parameter(parameters, CATEGORY)
        result = import_raster_to_planscape(
            RasterImportRequest(
                base_url=auth.get_base_url(auth.get_environment()),
                authcfg_id=authcfg_id,
                layer=layer,
                name=self.parameterAsString(parameters, NAME, context).strip(),
                dataset=self.parameterAsInt(parameters, DATASET, context),
                organization=self.parameterAsInt(parameters, ORGANIZATION, context),
                category=category,
                metadata=parse_metadata(self.parameterAsString(parameters, METADATA, context)),
            ),
            context,
            feedback,
        )
        return {
            DATALAYER_ID: result.datalayer_id,
            DATALAYER_NAME: result.datalayer_name,
            STYLE_ID: result.style_id,
            OUTPUT_FILE: result.output_file,
        }


def _optional_int_parameter(parameters: dict[str, Any], name: str) -> int | None:
    value = parameters.get(name) or None
    if value in (None, ""):
        return None
    return int(value)  # type: ignore[arg-type]
