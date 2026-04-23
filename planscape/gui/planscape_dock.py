from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QMenu, QTreeWidget, QTreeWidgetItem, QWidget
from qgis.utils import iface

from planscape import auth
from planscape.gui.auth_dialog import AuthDialog

ROOT_NODE_KIND = "root"
WORKSPACES_NODE_KIND = "workspaces"
LOGIN_NODE_KIND = "login"


class PlanscapeDockWidget(QDockWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Planscape", parent)
        self.setObjectName("PlanscapeDockWidget")

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.itemClicked.connect(self._handle_item_clicked)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        self.setWidget(self.tree)
        self.refresh_tree()

    def refresh_tree(self) -> None:
        self.tree.clear()

        root = QTreeWidgetItem([self._root_label()])
        root.setData(
            0,
            Qt.ItemDataRole.UserRole,
            LOGIN_NODE_KIND if not auth.is_authenticated() else ROOT_NODE_KIND,
        )
        self.tree.addTopLevelItem(root)

        if auth.is_authenticated():
            root.addChild(self._workspaces_item())

        root.setExpanded(True)
        self.tree.setCurrentItem(root)

    def focus_panel(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        del column
        if item.data(0, Qt.ItemDataRole.UserRole) != LOGIN_NODE_KIND:
            return

        dialog = AuthDialog(parent=iface.mainWindow())
        dialog.exec()
        self.refresh_tree()

    def _show_context_menu(self, position) -> None:
        item = self.tree.itemAt(position)
        if item is None:
            return

        menu = QMenu(self.tree)
        item_kind = item.data(0, Qt.ItemDataRole.UserRole)
        if item_kind == ROOT_NODE_KIND:
            menu.addAction(self._login_another_env_action())
            menu.addAction(self._logout_action())
        elif item_kind == WORKSPACES_NODE_KIND:
            menu.addAction(self._add_workspace_action())
        else:
            return

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _root_label(self) -> str:
        if not auth.is_authenticated():
            return "Click to login"
        return f"Planscape ({auth.get_environment()})"

    def _workspaces_item(self) -> QTreeWidgetItem:
        item = QTreeWidgetItem([f"Workspaces ({self._workspace_count()})"])
        item.setData(0, Qt.ItemDataRole.UserRole, WORKSPACES_NODE_KIND)
        return item

    def _workspace_count(self) -> int:
        # TODO: replace with an authenticated HTTP call once the workspace endpoint is defined.
        return 0

    def _add_workspace_action(self) -> QAction:
        action = QAction("Add workspace", self.tree)
        action.triggered.connect(self._add_workspace)
        return action

    def _login_another_env_action(self) -> QAction:
        action = QAction("Login another env", self.tree)
        action.triggered.connect(self._login_another_env)
        return action

    def _logout_action(self) -> QAction:
        action = QAction("Logout", self.tree)
        action.triggered.connect(self._logout)
        return action

    def _add_workspace(self) -> None:
        # TODO: open the add-workspace flow once the UI and API contract are defined.
        return None

    def _login_another_env(self) -> None:
        auth.sign_out()
        self.refresh_tree()

        dialog = AuthDialog(parent=iface.mainWindow())
        dialog.exec()
        self.refresh_tree()

    def _logout(self) -> None:
        auth.sign_out()
        self.refresh_tree()
