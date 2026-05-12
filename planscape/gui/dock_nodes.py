from __future__ import annotations

from dataclasses import dataclass

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication, QStyle, QTreeWidgetItem

from planscape.gui.behaviors import behavior_for
from planscape.models.domain import LoginNode, Model, NodeKind, Server, Workspace
from planscape.qgis_plugin_tools.tools.resources import resources_path

NODE_OBJECT_ROLE = Qt.ItemDataRole.UserRole
NODE_KIND_ROLE = Qt.ItemDataRole.UserRole + 1
LOADING_CHILD_LABEL = "Loading..."


@dataclass(frozen=True)
class DockNode:
    model: Model

    def node_kind(self) -> NodeKind:
        return self.model.kind

    def label(self) -> str:
        return self.model.node_label()

    def tree_item(self) -> QTreeWidgetItem:
        item = QTreeWidgetItem([self.label()])
        item.setData(0, NODE_OBJECT_ROLE, self.model)
        item.setData(0, NODE_KIND_ROLE, self.node_kind())
        icon = _node_icon(self.node_kind())
        if not icon.isNull():
            item.setIcon(0, icon)
        return item


def login_item() -> QTreeWidgetItem:
    return DockNode(LoginNode()).tree_item()


def server_item(server: Server) -> QTreeWidgetItem:
    return model_item(server)


def workspace_item(workspace: Workspace) -> QTreeWidgetItem:
    return model_item(workspace)


def model_item(model: Model) -> QTreeWidgetItem:
    item = DockNode(model).tree_item()
    if behavior_for(model).has_children:
        add_loading_child(item)
    return item


def add_loading_child(item: QTreeWidgetItem) -> None:
    item.addChild(loading_item())


def loading_item() -> QTreeWidgetItem:
    item = QTreeWidgetItem([LOADING_CHILD_LABEL])
    icon = _loading_icon()
    if not icon.isNull():
        item.setIcon(0, icon)
    return item


def _loading_icon() -> QIcon:
    icon = QIcon.fromTheme("view-refresh")
    if not icon.isNull():
        return icon

    app = QApplication.instance()
    if app is None:
        return QIcon()
    return app.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)


def _node_icon(kind: NodeKind) -> QIcon:
    icon_paths = {
        NodeKind.LOGIN: resources_path("icons", "planscape", "planscape-bw.png"),
        NodeKind.SERVER: resources_path("icons", "planscape", "planscape-color.png"),
        NodeKind.DATASET_COLLECTION: resources_path("icons", "planscape", "datasets.png"),
        NodeKind.DATALAYER_COLLECTION: resources_path("icons", "planscape", "datalayers.png"),
        NodeKind.MODULE_COLLECTION: resources_path("icons", "planscape", "modules.png"),
        NodeKind.STYLE_COLLECTION: resources_path("icons", "planscape", "styles.png"),
        NodeKind.USER_COLLECTION: resources_path("icons", "planscape", "users.png"),
    }
    if kind in icon_paths:
        return QIcon(icon_paths[kind])
    if kind == NodeKind.WORKSPACE:
        app = QApplication.instance()
        if app is not None:
            return app.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
    return QIcon()


def item_kind(item: QTreeWidgetItem) -> NodeKind | None:
    kind = item.data(0, NODE_KIND_ROLE)
    if kind is not None:
        return kind
    data = item.data(0, NODE_OBJECT_ROLE)
    return getattr(data, "kind", None)


def item_node(item: QTreeWidgetItem) -> object | None:
    return item.data(0, NODE_OBJECT_ROLE)
