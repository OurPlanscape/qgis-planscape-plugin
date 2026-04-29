from __future__ import annotations

from qgis.PyQt.QtWidgets import QDialog, QWidget

from planscape.qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS: QWidget
FORM_CLASS = load_ui("workspace_dialog.ui")


class WorkspaceDialog(QDialog, FORM_CLASS):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        workspace_id: str = "",
        name: str = "",
        visibility: str = "private",
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.visibility_combo.addItems(["public", "private"])
        self.id_input.setText(workspace_id)
        self.name_input.setText(name)
        self.visibility_combo.setCurrentText(visibility)
        self.name_input.setFocus()

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)

    def workspace_name(self) -> str:
        return self.name_input.text().strip()

    def workspace_id(self) -> str:
        return self.id_input.text().strip()

    def workspace_visibility(self) -> str:
        return self.visibility_combo.currentText()
