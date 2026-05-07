from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication, QDockWidget, QMenu, QTreeWidget, QTreeWidgetItem, QWidget
from qgis.utils import iface

from planscape import auth
from planscape.api.exceptions import WorkspaceApiError
from planscape.api.workspace import list_workspaces_request
from planscape.gui.auth_dialog import AuthDialog
from planscape.gui.behaviors import DockContext, behavior_for
from planscape.gui.dock_nodes import (
    add_loading_child,
    item_kind,
    item_node,
    login_item,
    model_item,
    server_item,
)
from planscape.models.domain import Model, NodeKind, Server, Workspace


class PlanscapeDockWidget(QDockWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Planscape", parent)
        self.setObjectName("PlanscapeDockWidget")

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.itemClicked.connect(self._handle_item_clicked)
        self.tree.itemDoubleClicked.connect(self._handle_item_double_clicked)
        self.tree.itemExpanded.connect(self._load_item_children)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        self.setWidget(self.tree)
        self.refresh_tree()

    def refresh_tree(self) -> None:
        self.tree.clear()
        self._restore_authenticated_session()

        root = self._root_item()
        self.tree.addTopLevelItem(root)

        root.setExpanded(True)
        if isinstance(item_node(root), Server):
            self._refresh_item(root)
        else:
            self._load_item_children(root)
        self.tree.setCurrentItem(root)

    def focus_panel(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        del column
        if item_kind(item) != NodeKind.LOGIN:
            return

        dialog = AuthDialog(parent=iface.mainWindow())
        dialog.exec()
        self.refresh_tree()

    def _handle_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        del column
        node = item_node(item)
        if not isinstance(node, Model):
            return
        behavior_for(node).double_clicked(node, self._context(), item)

    def _show_context_menu(self, position) -> None:
        item = self.tree.itemAt(position)
        if item is None:
            return

        node = item_node(item)
        if not isinstance(node, Model):
            return

        actions = behavior_for(node).actions(node, self._context(), item)
        if not actions:
            return

        menu = QMenu(self.tree)
        for action in actions:
            menu.addAction(action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _root_item(self) -> QTreeWidgetItem:
        if not auth.is_authenticated():
            return login_item()
        environment = auth.get_environment()
        server = Server(name="Planscape", env=environment)
        return self._server_item(server)

    def _server_item(self, server: Server) -> QTreeWidgetItem:
        return server_item(server)

    def _restore_authenticated_session(self) -> None:
        if not auth.is_authenticated():
            auth.restore_authenticated_session()

    def _context(self) -> DockContext:
        return DockContext(
            tree=self.tree,
            parent=self,
            refresh_node=self._refresh_item,
            login_another_env=self._login_another_env,
            logout=self._logout,
        )

    def _load_item_children(self, item: QTreeWidgetItem) -> None:
        self._replace_item_children(item, expanded_keys=set())

    def _refresh_item(self, item: QTreeWidgetItem) -> None:
        node = item_node(item)
        if isinstance(node, Server):
            node.workspaces = self._load_workspaces(node.env)
        expanded_keys = self._expanded_node_keys(item)
        self._replace_item_children(item, expanded_keys=expanded_keys)

    def _load_workspaces(self, environment: str) -> list[Workspace]:
        try:
            return list_workspaces_request(auth.get_base_url(environment), auth.ensure_authenticated())
        except WorkspaceApiError:
            return []

    def _replace_item_children(self, item: QTreeWidgetItem, *, expanded_keys: set[str]) -> None:
        node = item_node(item)
        if not isinstance(node, Model):
            return

        behavior = behavior_for(node)
        if not behavior.has_children:
            return

        item.takeChildren()
        add_loading_child(item)
        QApplication.processEvents()

        item.takeChildren()
        for child_model in behavior.load_children(node, self._context()):
            child_item = model_item(child_model)
            item.addChild(child_item)
            if child_model.node_key() in expanded_keys:
                child_item.setExpanded(True)
                self._replace_item_children(child_item, expanded_keys=expanded_keys)
        self.tree.viewport().update()
        QApplication.processEvents()

    def _expanded_node_keys(self, item: QTreeWidgetItem) -> set[str]:
        keys: set[str] = set()
        self._collect_expanded_node_keys(item, keys)
        return keys

    def _collect_expanded_node_keys(self, item: QTreeWidgetItem, keys: set[str]) -> None:
        node = item_node(item)
        if isinstance(node, Model) and item.isExpanded():
            keys.add(node.node_key())
        for index in range(item.childCount()):
            self._collect_expanded_node_keys(item.child(index), keys)

    def _login_another_env(self) -> None:
        auth.sign_out()
        self.refresh_tree()

        dialog = AuthDialog(parent=iface.mainWindow())
        dialog.exec()
        self.refresh_tree()

    def _logout(self) -> None:
        auth.sign_out()
        self.refresh_tree()
