from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication, QDialog, QWidget

from planscape import auth
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginException
from planscape.qgis_plugin_tools.tools.messages import MessageBarLogger
from planscape.qgis_plugin_tools.tools.resources import load_ui, plugin_name

FORM_CLASS: QWidget
FORM_CLASS = load_ui("auth_dialog.ui")


class AuthDialog(QDialog, FORM_CLASS):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self._message_bar = MessageBarLogger(plugin_name())

        self.environment_combo.addItems(auth.environment_names())
        self.email_input.setText(auth.get_saved_email())
        self.environment_combo.setCurrentText(auth.get_environment())

        self.password_input.setEchoMode(self.password_input.EchoMode.Password)

        self.sign_in_button.clicked.connect(self._sign_in)
        self.sign_out_button.clicked.connect(self._sign_out)
        self.cancel_button.clicked.connect(self.reject)
        self.environment_combo.currentTextChanged.connect(self._update_status)

        self._update_status()

    def _sign_in(self) -> None:
        email = self.email_input.text().strip()
        password = self.password_input.text()
        environment = self.environment_combo.currentText()

        self._set_busy(is_busy=True)
        try:
            auth.sign_in(email, password, environment)
        except (auth.PlanscapeAuthError, QgsPluginException) as exc:
            message = str(exc)
            self.status_label.setText(message)
            self._message_bar.error("Planscape sign-in failed", message)
            return
        finally:
            self._set_busy(is_busy=False)

        self.password_input.clear()
        self._update_status()
        self._message_bar.info(
            "Planscape authentication succeeded",
            f"Signed in to the {environment} environment.",
            success=True,
        )
        self.accept()

    def _sign_out(self) -> None:
        auth.sign_out()
        self.password_input.clear()
        self._update_status()
        self._message_bar.info("Planscape token cleared", "Signed out of the current session.")

    def _set_busy(self, *, is_busy: bool) -> None:
        self.sign_in_button.setEnabled(not is_busy)
        self.sign_out_button.setEnabled(not is_busy and auth.is_authenticated())
        self.environment_combo.setEnabled(not is_busy)
        self.email_input.setEnabled(not is_busy)
        self.password_input.setEnabled(not is_busy)
        if is_busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def _update_status(self) -> None:
        environment = self.environment_combo.currentText() or auth.get_environment()
        if auth.is_authenticated():
            self.status_label.setText(f"Authenticated for the {environment} environment.")
            self.sign_out_button.setEnabled(True)
        else:
            self.status_label.setText(f"Not authenticated. Sign in to the {environment} environment.")
            self.sign_out_button.setEnabled(False)
