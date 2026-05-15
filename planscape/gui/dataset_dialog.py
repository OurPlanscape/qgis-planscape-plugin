from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIntValidator
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem, QWidget

from planscape.qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS: QWidget
FORM_CLASS = load_ui("dataset_dialog.ui")
AVAILABLE_DATASET_MODULES = ["map", "forsys", "prioritize_sub_units"]
DEFAULT_DATASET_MODULES = list(AVAILABLE_DATASET_MODULES)
PREFERRED_DISPLAY_TYPES = ["MAIN_DATALAYERS", "BASE_DATALAYERS"]
SELECTION_TYPES = ["SINGLE", "MULTIPLE"]


class DatasetDialog(QDialog, FORM_CLASS):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        dataset_id: str = "",
        name: str = "",
        visibility: str = "private",
        preferred_display_type: str = "MAIN_DATALAYERS",
        selection_type: str = "SINGLE",
        organization: int | str | None = None,
        version: str = "",
        modules: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.visibility_combo.addItems(["public", "private"])
        self.preferred_display_type_combo.addItems(PREFERRED_DISPLAY_TYPES)
        self.selection_type_combo.addItems(SELECTION_TYPES)
        self.organization_input.setValidator(QIntValidator(0, 2147483647, self))
        self.id_input.setText(dataset_id)
        self.name_input.setText(name)
        self.visibility_combo.setCurrentText(visibility)
        self.preferred_display_type_combo.setCurrentText(preferred_display_type)
        self.selection_type_combo.setCurrentText(selection_type)
        self.organization_input.setText("" if organization is None else str(organization))
        self.version_input.setText(version)
        self._populate_modules(modules or DEFAULT_DATASET_MODULES)
        self.name_input.setFocus()

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)

    def dataset_name(self) -> str:
        return self.name_input.text().strip()

    def dataset_id(self) -> str:
        return self.id_input.text().strip()

    def dataset_visibility(self) -> str:
        return self.visibility_combo.currentText()

    def dataset_preferred_display_type(self) -> str:
        return self.preferred_display_type_combo.currentText()

    def dataset_selection_type(self) -> str:
        return self.selection_type_combo.currentText()

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

    def dataset_modules(self) -> list[str]:
        modules = []
        for index in range(self.modules_input.count()):
            item = self.modules_input.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                modules.append(item.text())
        return modules

    def _populate_modules(self, selected_modules: list[str]) -> None:
        selected = set(selected_modules)
        self.modules_input.clear()
        for module in AVAILABLE_DATASET_MODULES:
            item = QListWidgetItem(module)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if module in selected else Qt.CheckState.Unchecked)
            self.modules_input.addItem(item)
