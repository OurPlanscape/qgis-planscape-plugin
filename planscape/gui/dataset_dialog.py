from __future__ import annotations

from qgis.PyQt.QtGui import QIntValidator
from qgis.PyQt.QtWidgets import QDialog, QWidget

from planscape.qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS: QWidget
FORM_CLASS = load_ui("dataset_dialog.ui")
DEFAULT_DATASET_MODULES = "forsys,map,prioritize_sub_units"


class DatasetDialog(QDialog, FORM_CLASS):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        dataset_id: str = "",
        name: str = "",
        visibility: str = "private",
        organization: int | str | None = None,
        version: str = "",
        modules: str = DEFAULT_DATASET_MODULES,
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.visibility_combo.addItems(["public", "private"])
        self.organization_input.setValidator(QIntValidator(0, 2147483647, self))
        self.id_input.setText(dataset_id)
        self.name_input.setText(name)
        self.visibility_combo.setCurrentText(visibility)
        self.organization_input.setText("" if organization is None else str(organization))
        self.version_input.setText(version)
        self.modules_input.setText(modules)
        self.name_input.setFocus()

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)

    def dataset_name(self) -> str:
        return self.name_input.text().strip()

    def dataset_id(self) -> str:
        return self.id_input.text().strip()

    def dataset_visibility(self) -> str:
        return self.visibility_combo.currentText()

    def dataset_organization(self) -> int | None:
        value = self.organization_input.text().strip()
        if not value:
            return None
        return int(value)

    def dataset_version(self) -> str | None:
        value = self.version_input.text().strip()
        if not value:
            return None
        return value

    def dataset_modules(self) -> str:
        return self.modules_input.text().strip()
