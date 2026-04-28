from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget

from planscape.gui.planscape_dock import WORKSPACES_NODE_KIND, PlanscapeDockWidget
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


def test_planscape_dock_shows_environment_when_authenticated(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()

    assert dock.tree.topLevelItem(0).text(0) == "Planscape (catalog)"
    assert dock.tree.topLevelItem(0).child(0).text(0) == "Workspaces (0)"


def test_planscape_dock_workspaces_node_has_expected_kind(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    workspaces = dock.tree.topLevelItem(0).child(0)

    assert workspaces.data(0, Qt.ItemDataRole.UserRole) == WORKSPACES_NODE_KIND


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
    assert dock.tree.topLevelItem(0).child(0).text(0) == "Workspaces (0)"


def test_planscape_dock_workspaces_context_menu_has_add_action(qgis_app, monkeypatch):
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
    workspaces_rect = dock.tree.visualItemRect(dock.tree.topLevelItem(0).child(0))

    dock._show_context_menu(workspaces_rect.center())

    assert captured["actions"] == ["Create new Workspace"]


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

    assert captured["actions"] == ["Login another env", "Logout"]


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
