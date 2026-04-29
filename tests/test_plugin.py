from qgis.PyQt.QtWidgets import QWidget

from planscape.gui.dock_nodes import NODE_KIND_ROLE, NODE_OBJECT_ROLE
from planscape.gui.planscape_dock import PlanscapeDockWidget
from planscape.models.domain import Category, DataLayer, Dataset, LoginNode, NodeKind, Server, Style, User, Workspace
from planscape.plugin import Plugin
from planscape.qgis_plugin_tools.tools.resources import plugin_name


def test_plugin_name():
    assert plugin_name() == "Planscape"


def test_plugin_init_gui_creates_and_shows_dock(monkeypatch):
    state = {"added_provider": False, "added_dock": None, "shown": False}

    class FakeRegistry:
        def addProvider(self, provider):
            state["added_provider"] = provider is not None

        def removeProvider(self, provider):
            del provider

    class FakeQgsApplication:
        @staticmethod
        def processingRegistry():
            return FakeRegistry()

    class FakeDock:
        def __init__(self, parent=None):
            self.parent = parent

        def focus_panel(self):
            state["shown"] = True

    class FakeIface:
        def __init__(self):
            self.window = QWidget()

        def mainWindow(self):
            return self.window

        def addDockWidget(self, area, widget):
            state["added_dock"] = (area, widget)

        def addPluginToMenu(self, menu, action):
            del menu, action

    monkeypatch.setattr("planscape.plugin.QgsApplication", FakeQgsApplication)
    monkeypatch.setattr("planscape.plugin.PlanscapeDockWidget", FakeDock)
    monkeypatch.setattr("planscape.plugin.iface", FakeIface())

    plugin = Plugin()

    plugin.initGui()

    assert state["added_provider"] is True
    assert state["added_dock"] is not None
    assert isinstance(plugin.dock_widget, FakeDock)
    assert state["shown"] is True


def test_plugin_run_focuses_existing_dock(monkeypatch):  # noqa: ARG001
    state = {"focused": False}

    class FakeDock:
        def focus_panel(self):
            state["focused"] = True

    plugin = Plugin()
    plugin.dock_widget = FakeDock()

    plugin.run()

    assert state == {"focused": True}


def test_plugin_unload_removes_dock(monkeypatch):
    state = {"removed_provider": False, "removed_dock": None, "menu_removed": 0, "toolbar_removed": 0}

    class FakeRegistry:
        def addProvider(self, provider):
            del provider

        def removeProvider(self, provider):
            state["removed_provider"] = provider is not None

    class FakeQgsApplication:
        @staticmethod
        def processingRegistry():
            return FakeRegistry()

    class FakeDock:
        def deleteLater(self):
            return None

    class FakeIface:
        def removeDockWidget(self, widget):
            state["removed_dock"] = widget

        def removePluginMenu(self, menu, action):
            del menu, action
            state["menu_removed"] += 1

        def removeToolBarIcon(self, action):
            del action
            state["toolbar_removed"] += 1

    monkeypatch.setattr("planscape.plugin.QgsApplication", FakeQgsApplication)
    monkeypatch.setattr("planscape.plugin.iface", FakeIface())

    plugin = Plugin()
    plugin.dock_widget = FakeDock()  # type: ignore
    plugin.actions = [object()]

    plugin.unload()

    assert state["removed_provider"] is True
    assert state["removed_dock"] is not None
    assert plugin.dock_widget is None
    assert state["menu_removed"] == 1
    assert state["toolbar_removed"] == 1


def test_planscape_dock_shows_login_root_when_unauthenticated(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: False)

    dock = PlanscapeDockWidget()

    assert dock.tree.topLevelItem(0).text(0) == "Click to login"
    assert dock.tree.topLevelItem(0).data(0, NODE_KIND_ROLE) == NodeKind.LOGIN
    assert dock.tree.topLevelItem(0).data(0, NODE_OBJECT_ROLE) == LoginNode()


def test_planscape_dock_shows_environment_when_authenticated(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()

    assert dock.tree.topLevelItem(0).text(0) == "Planscape (catalog)"
    assert dock.tree.topLevelItem(0).data(0, NODE_KIND_ROLE) == NodeKind.SERVER
    assert dock.tree.topLevelItem(0).data(0, NODE_OBJECT_ROLE) == Server(name="Planscape", env="catalog")
    assert dock.tree.topLevelItem(0).childCount() == 0


def test_planscape_dock_server_lists_workspace_children(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog", workspaces=[Workspace(id=7, name="Regional Plan")])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)

    assert workspace.text(0) == "Regional Plan"
    assert workspace.data(0, NODE_KIND_ROLE) == NodeKind.WORKSPACE
    assert workspace.data(0, NODE_OBJECT_ROLE) == Workspace(id=7, name="Regional Plan")


def test_planscape_dock_refresh_reloads_mutated_server_children(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog")
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    root = dock.tree.topLevelItem(0)
    dock._load_item_children(root)

    server.workspaces.append(Workspace(id=7, name="Regional Plan"))
    dock._refresh_item(root)

    assert root.childCount() == 1
    assert root.child(0).text(0) == "Regional Plan"


def test_planscape_dock_workspace_expands_to_collection_nodes(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    workspace_model = Workspace(
        id=7,
        name="Regional Plan",
        datasets=[Dataset(id=20, name="Base Data")],
        styles=[Style(id=30, name="Default")],
        users=[User(id=40, name="Planner")],
    )
    server = Server(name="Planscape", env="catalog", workspaces=[workspace_model])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)

    dock._load_item_children(workspace)

    assert [workspace.child(index).text(0) for index in range(workspace.childCount())] == [
        "Datasets",
        "Styles",
        "Users",
    ]
    assert [workspace.child(index).data(0, NODE_KIND_ROLE) for index in range(workspace.childCount())] == [
        NodeKind.DATASET_COLLECTION,
        NodeKind.STYLE_COLLECTION,
        NodeKind.USER_COLLECTION,
    ]


def test_planscape_dock_dataset_expands_to_collection_nodes(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    dataset_model = Dataset(
        id=20,
        name="Base Data",
        datalayers=[DataLayer(id=30, name="Roads")],
        categories=[Category(id=40, name="Transportation")],
    )
    workspace_model = Workspace(id=7, name="Regional Plan", datasets=[dataset_model])
    server = Server(name="Planscape", env="catalog", workspaces=[workspace_model])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    datasets = workspace.child(0)
    dock._load_item_children(datasets)
    dataset = datasets.child(0)

    dock._load_item_children(dataset)

    assert [dataset.child(index).text(0) for index in range(dataset.childCount())] == ["Data Layers", "Categories"]
    assert [dataset.child(index).data(0, NODE_KIND_ROLE) for index in range(dataset.childCount())] == [
        NodeKind.DATALAYER_COLLECTION,
        NodeKind.CATEGORY_COLLECTION,
    ]


def test_planscape_dock_click_login_opens_auth_and_refreshes(qgis_app, monkeypatch):
    assert qgis_app is not None

    auth_state = {"value": False}
    state = {"executed": False}

    class FakeDialog:
        def __init__(self, parent=None):
            del parent

        def exec(self):
            state["executed"] = True
            auth_state["value"] = True

    monkeypatch.setattr("planscape.gui.planscape_dock.AuthDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: auth_state["value"])
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "staging")

    dock = PlanscapeDockWidget()
    item = dock.tree.topLevelItem(0)

    dock._handle_item_clicked(item, 0)

    assert state["executed"] is True
    assert dock.tree.topLevelItem(0).text(0) == "Planscape (staging)"
    assert dock.tree.topLevelItem(0).childCount() == 0


def test_planscape_dock_server_context_menu_has_add_workspace_action(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(action.text())

        def exec(self, position):
            del position

    monkeypatch.setattr("planscape.gui.planscape_dock.QMenu", FakeMenu)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    dock.show()
    root_rect = dock.tree.visualItemRect(dock.tree.topLevelItem(0))

    dock._show_context_menu(root_rect.center())

    assert captured["actions"] == ["Create new Workspace", "Refresh", "Login another env", "Logout"]


def test_planscape_dock_collection_context_menu_has_refresh_action(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(action.text())

        def exec(self, position):
            del position

    monkeypatch.setattr("planscape.gui.planscape_dock.QMenu", FakeMenu)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    workspace_model = Workspace(id=7, name="Regional Plan")
    server = Server(name="Planscape", env="catalog", workspaces=[workspace_model])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    datasets = workspace.child(0)

    def item_at(position):
        del position
        return datasets

    monkeypatch.setattr(dock.tree, "itemAt", item_at)

    dock._show_context_menu(dock.tree.rect().center())

    assert captured["actions"] == ["New Dataset", "Refresh"]


def test_planscape_dock_add_workspace_opens_workspace_dialog(qgis_app, monkeypatch):
    assert qgis_app is not None

    state = {"executed": False}

    class FakeDialog:
        def __init__(self, parent=None):
            del parent

        def exec(self):
            state["executed"] = True

    monkeypatch.setattr("planscape.gui.planscape_dock.WorkspaceDialog", FakeDialog)

    dock = PlanscapeDockWidget()

    dock._add_workspace()

    assert state["executed"] is True


def test_planscape_dock_root_context_menu_has_auth_actions_in_order(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(action.text())

        def exec(self, position):
            del position

    monkeypatch.setattr("planscape.gui.planscape_dock.QMenu", FakeMenu)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    dock.show()
    root_rect = dock.tree.visualItemRect(dock.tree.topLevelItem(0))

    dock._show_context_menu(root_rect.center())

    assert captured["actions"] == ["Create new Workspace", "Refresh", "Login another env", "Logout"]


def test_planscape_dock_login_another_env_signs_out_opens_auth_and_refreshes(qgis_app, monkeypatch):
    assert qgis_app is not None

    state = {"sign_out_calls": 0, "dialog_exec": 0, "authenticated": True}

    class FakeDialog:
        def __init__(self, parent=None):
            del parent

        def exec(self):
            state["dialog_exec"] += 1

    def fake_sign_out() -> None:
        state["sign_out_calls"] += 1
        state["authenticated"] = False

    monkeypatch.setattr("planscape.gui.planscape_dock.AuthDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.sign_out", fake_sign_out)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: state["authenticated"])
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()

    dock._login_another_env()

    assert state["sign_out_calls"] == 1
    assert state["dialog_exec"] == 1
    assert dock.tree.topLevelItem(0).text(0) == "Click to login"


def test_planscape_dock_logout_signs_out_and_refreshes(qgis_app, monkeypatch):
    assert qgis_app is not None

    state = {"sign_out_calls": 0, "authenticated": True}

    def fake_sign_out() -> None:
        state["sign_out_calls"] += 1
        state["authenticated"] = False

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.sign_out", fake_sign_out)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: state["authenticated"])
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()

    dock._logout()

    assert state["sign_out_calls"] == 1
    assert dock.tree.topLevelItem(0).text(0) == "Click to login"
    assert dock.tree.topLevelItem(0).text(0) == "Click to login"
