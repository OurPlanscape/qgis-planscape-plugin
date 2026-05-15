import pytest
from qgis.PyQt.QtWidgets import QWidget

from planscape.api.exceptions import DatasetAPIError, WorkspaceAPIError
from planscape.gui.behaviors import behavior_for
from planscape.gui.dock_nodes import LOADING_CHILD_LABEL, NODE_KIND_ROLE, NODE_OBJECT_ROLE, model_item
from planscape.gui.planscape_dock import PlanscapeDockWidget
from planscape.models.domain import (
    Category,
    DataLayer,
    DataLayerCollection,
    Dataset,
    DatasetCollection,
    LoginNode,
    Module,
    NodeKind,
    Server,
    Style,
    StyleCollection,
    User,
    UserCollection,
    Workspace,
    WorkspaceVisibility,
)
from planscape.plugin import Plugin
from planscape.qgis_plugin_tools.tools.resources import plugin_name


@pytest.fixture(autouse=True)
def fake_workspace_api(monkeypatch):
    monkeypatch.setattr(
        "planscape.gui.planscape_dock.auth.get_base_url", lambda environment: f"https://{environment}.example"
    )
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.restore_authenticated_session", lambda: False)

    def fake_list_workspaces_request(base_url: str, authcfg_id: str) -> list[Workspace]:
        del base_url, authcfg_id
        return []

    monkeypatch.setattr("planscape.gui.planscape_dock.list_workspaces_request", fake_list_workspaces_request)
    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.auth.get_base_url",
        lambda environment: f"https://{environment}.example",
    )
    monkeypatch.setattr("planscape.gui.behaviors.dataset_collection.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.behaviors.dataset_collection.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr(
        "planscape.gui.behaviors.style_collection.auth.get_base_url",
        lambda environment: f"https://{environment}.example",
    )
    monkeypatch.setattr("planscape.gui.behaviors.style_collection.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.behaviors.style_collection.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr(
        "planscape.gui.behaviors.user_collection.auth.get_base_url",
        lambda environment: f"https://{environment}.example",
    )
    monkeypatch.setattr("planscape.gui.behaviors.user_collection.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.behaviors.user_collection.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset.auth.get_base_url",
        lambda environment: f"https://{environment}.example",
    )
    monkeypatch.setattr("planscape.gui.behaviors.dataset.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.behaviors.dataset.auth.get_environment", lambda: "catalog")

    def empty_workspace_children(*args):
        del args
        return []

    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.list_workspace_datasets_request",
        empty_workspace_children,
    )
    monkeypatch.setattr(
        "planscape.gui.behaviors.style_collection.list_workspace_styles_request",
        empty_workspace_children,
    )
    monkeypatch.setattr(
        "planscape.gui.behaviors.user_collection.list_workspace_users_request",
        empty_workspace_children,
    )

    class EmptyBrowseTree:
        def __init__(self):
            self.categories = []
            self.datalayers = []

    def empty_browse_tree(*args):
        del args
        return EmptyBrowseTree()

    monkeypatch.setattr("planscape.gui.behaviors.dataset.browse_dataset_request", empty_browse_tree)


def test_plugin_name():
    assert plugin_name() == "Planscape"


def action_by_text(actions, text):
    for action in actions:
        if action.text() == text:
            return action
    pytest.fail(f"Action not found: {text}")


def menu_action_label(action):
    if action.isSeparator():
        return "<separator>"
    return action.text()


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
    assert not dock.tree.topLevelItem(0).icon(0).isNull()


def test_planscape_dock_shows_environment_when_authenticated(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()

    assert dock.tree.topLevelItem(0).text(0) == "Planscape (catalog)"
    assert dock.tree.topLevelItem(0).data(0, NODE_KIND_ROLE) == NodeKind.SERVER
    assert dock.tree.topLevelItem(0).data(0, NODE_OBJECT_ROLE) == Server(name="Planscape", env="catalog")
    assert not dock.tree.topLevelItem(0).icon(0).isNull()
    assert dock.tree.topLevelItem(0).childCount() == 0


def test_planscape_dock_loads_workspaces_when_authenticated(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    def fake_list_workspaces_request(base_url: str, authcfg_id: str) -> list[Workspace]:
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        return [Workspace(id=7, name="Regional Plan")]

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr("planscape.gui.planscape_dock.list_workspaces_request", fake_list_workspaces_request)

    dock = PlanscapeDockWidget()
    root = dock.tree.topLevelItem(0)

    assert captured == {"base_url": "https://catalog.example", "authcfg_id": "authcfg-id"}
    assert root.childCount() == 1
    assert root.child(0).text(0) == "Regional Plan"
    assert root.child(0).data(0, NODE_OBJECT_ROLE) == Workspace(id=7, name="Regional Plan")


def test_planscape_dock_restores_saved_session_and_loads_workspaces(qgis_app, monkeypatch):
    assert qgis_app is not None

    auth_state = {"authenticated": False}
    captured = {}

    def fake_restore_authenticated_session() -> bool:
        auth_state["authenticated"] = True
        return True

    def fake_list_workspaces_request(base_url: str, authcfg_id: str) -> list[Workspace]:
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        return [Workspace(id=8, name="Saved Session Workspace")]

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: auth_state["authenticated"])
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr(
        "planscape.gui.planscape_dock.auth.restore_authenticated_session",
        fake_restore_authenticated_session,
    )
    monkeypatch.setattr("planscape.gui.planscape_dock.list_workspaces_request", fake_list_workspaces_request)

    dock = PlanscapeDockWidget()
    root = dock.tree.topLevelItem(0)

    assert root.text(0) == "Planscape (catalog)"
    assert captured == {"base_url": "https://catalog.example", "authcfg_id": "authcfg-id"}
    assert root.childCount() == 1
    assert root.child(0).text(0) == "Saved Session Workspace"


def test_planscape_dock_failed_session_restore_shows_login_root(qgis_app, monkeypatch):
    assert qgis_app is not None

    state = {"restore_called": False}

    def fake_restore_authenticated_session() -> bool:
        state["restore_called"] = True
        return False

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: False)
    monkeypatch.setattr(
        "planscape.gui.planscape_dock.auth.restore_authenticated_session",
        fake_restore_authenticated_session,
    )

    dock = PlanscapeDockWidget()

    assert state["restore_called"] is True
    assert dock.tree.topLevelItem(0).text(0) == "Click to login"
    assert dock.tree.topLevelItem(0).data(0, NODE_KIND_ROLE) == NodeKind.LOGIN


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
    assert not workspace.icon(0).isNull()


def test_planscape_dock_refresh_reloads_server_children_from_api(qgis_app, monkeypatch):
    assert qgis_app is not None

    calls = {"count": 0}

    def fake_list_workspaces_request(base_url: str, authcfg_id: str) -> list[Workspace]:
        del base_url, authcfg_id
        calls["count"] += 1
        if calls["count"] == 1:
            return []
        return [Workspace(id=7, name="Regional Plan")]

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr("planscape.gui.planscape_dock.list_workspaces_request", fake_list_workspaces_request)

    dock = PlanscapeDockWidget()
    root = dock.tree.topLevelItem(0)

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


def test_workspace_child_collection_labels_include_counts(qgis_app):
    assert qgis_app is not None

    dock = PlanscapeDockWidget()
    parent = model_item(Workspace(id=7, name="Regional Plan", dataset_count=3, style_count=2, user_count=5))
    dock.tree.clear()
    dock.tree.addTopLevelItem(parent)

    dock._load_item_children(parent)

    assert [parent.child(index).text(0) for index in range(parent.childCount())] == [
        "Datasets (3)",
        "Styles (2)",
        "Users (5)",
    ]


def test_expandable_model_items_show_loading_icon(qgis_app):
    assert qgis_app is not None

    item = model_item(Workspace(id=7, name="Regional Plan"))

    assert item.childCount() == 1
    assert item.child(0).text(0) == LOADING_CHILD_LABEL
    assert not item.child(0).icon(0).isNull()


def test_collection_model_items_show_distinguishing_icons(qgis_app):
    assert qgis_app is not None

    items = [
        model_item(DatasetCollection()),
        model_item(DataLayerCollection()),
        model_item(StyleCollection()),
        model_item(UserCollection()),
    ]

    assert all(not item.icon(0).isNull() for item in items)


def test_resource_model_items_without_specific_icons_do_not_show_distinguishing_icons(qgis_app):
    assert qgis_app is not None

    items = [
        model_item(Dataset(id=20, name="Dataset A")),
        model_item(DataLayer(id=30, name="DataLayer A")),
        model_item(Style(id=40, name="Style A")),
    ]

    assert all(item.icon(0).isNull() for item in items)


def test_module_and_typed_datalayer_model_items_show_specific_icons(qgis_app):
    assert qgis_app is not None

    items = [
        model_item(Module(name="map")),
        model_item(Module(name="forsys")),
        model_item(DataLayer(id=30, name="Raster", type="RASTER")),
        model_item(DataLayer(id=31, name="Vector", type="VECTOR")),
    ]

    assert all(not item.icon(0).isNull() for item in items)


def test_planscape_dock_repaints_loading_item_before_loading_children(qgis_app, monkeypatch):
    assert qgis_app is not None

    calls = []

    def fake_process_events():
        calls.append("process_events")

    def fake_load_children(self, model, context):
        del self, model, context
        calls.append("load_children")
        return [Workspace(id=7, name="Regional Plan")]

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: False)
    monkeypatch.setattr("planscape.gui.planscape_dock.QApplication.processEvents", fake_process_events)
    monkeypatch.setattr("planscape.gui.behaviors.workspace.WorkspaceBehavior.load_children", fake_load_children)

    dock = PlanscapeDockWidget()
    dock.tree.clear()
    dock.tree.addTopLevelItem(model_item(Workspace(id=8, name="Source Workspace")))

    dock._load_item_children(dock.tree.topLevelItem(0))

    assert calls == ["process_events", "load_children", "process_events"]


def test_planscape_dock_dataset_expands_to_data_layers_collection(qgis_app, monkeypatch):
    assert qgis_app is not None

    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    dataset_model = Dataset(id=20, name="Base Data", modules=["map", "forsys"])

    def fake_list_workspace_datasets_request(base_url, authcfg_id, workspace_id):
        del base_url, authcfg_id, workspace_id
        return [dataset_model]

    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.list_workspace_datasets_request",
        fake_list_workspace_datasets_request,
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

    assert [dataset.child(index).text(0) for index in range(dataset.childCount())] == ["Modules", "Data Layers"]
    assert [dataset.child(index).data(0, NODE_KIND_ROLE) for index in range(dataset.childCount())] == [
        NodeKind.MODULE_COLLECTION,
        NodeKind.DATALAYER_COLLECTION,
    ]
    modules = dataset.child(0)
    dock._load_item_children(modules)
    assert [modules.child(index).text(0) for index in range(modules.childCount())] == ["map", "forsys"]


def test_planscape_dock_dataset_browse_builds_nested_datalayer_tree(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class BrowseTree:
        def __init__(self):
            self.categories = [
                Category(
                    name="Category A",
                    path=["Category A"],
                    datalayers=[DataLayer(id=30, name="DataLayer A1")],
                ),
                Category(
                    name="Category B",
                    path=["Category B"],
                    categories=[
                        Category(
                            name="Category B1",
                            path=["Category B", "Category B1"],
                            datalayers=[DataLayer(id=31, name="DataLayer B1A")],
                        )
                    ],
                    datalayers=[DataLayer(id=32, name="DataLayer B1")],
                ),
            ]
            self.datalayers = []

    def fake_browse_dataset_request(base_url, authcfg_id, dataset_id):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["dataset_id"] = dataset_id
        return BrowseTree()

    monkeypatch.setattr("planscape.gui.behaviors.dataset.browse_dataset_request", fake_browse_dataset_request)

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog", workspaces=[Workspace(id=7, name="Regional Plan")])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    datasets = workspace.child(0)

    def fake_list_workspace_datasets_request(base_url, authcfg_id, workspace_id):
        del base_url, authcfg_id, workspace_id
        return [Dataset(id=20, name="Dataset A")]

    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.list_workspace_datasets_request",
        fake_list_workspace_datasets_request,
    )
    dock._load_item_children(datasets)
    dataset = datasets.child(0)

    dock._load_item_children(dataset)
    datalayers = dataset.child(1)
    dock._load_item_children(datalayers)
    category_b = datalayers.child(1)
    dock._load_item_children(category_b)
    category_b1 = category_b.child(0)
    dock._load_item_children(category_b1)

    assert captured == {"base_url": "https://catalog.example", "authcfg_id": "authcfg-id", "dataset_id": 20}
    assert datalayers.text(0) == "Data Layers"
    assert [datalayers.child(index).text(0) for index in range(datalayers.childCount())] == [
        "Category A",
        "Category B",
    ]
    assert [category_b.child(index).text(0) for index in range(category_b.childCount())] == [
        "Category B1",
        "DataLayer B1",
    ]
    assert [category_b1.child(index).text(0) for index in range(category_b1.childCount())] == ["DataLayer B1A"]


def test_planscape_dock_dataset_browse_error_returns_empty_data_layers(qgis_app, monkeypatch):
    assert qgis_app is not None

    def fake_browse_dataset_request(base_url, authcfg_id, dataset_id):
        del base_url, authcfg_id, dataset_id
        message = "failed"
        raise DatasetAPIError(message)

    monkeypatch.setattr("planscape.gui.behaviors.dataset.browse_dataset_request", fake_browse_dataset_request)

    dock = PlanscapeDockWidget()
    item = model_item(Dataset(id=20, name="Dataset A"))
    dock.tree.clear()
    dock.tree.addTopLevelItem(item)

    dock._load_item_children(item)
    datalayers = item.child(1)
    dock._load_item_children(datalayers)

    assert datalayers.text(0) == "Data Layers"
    assert datalayers.childCount() == 0


def test_planscape_dock_double_click_dispatches_to_datalayer_behavior(qgis_app, monkeypatch):
    assert qgis_app is not None

    calls = []

    def fake_double_clicked(self, model, context, item):
        del self, context, item
        calls.append(model)

    monkeypatch.setattr("planscape.gui.behaviors.datalayer.DataLayerBehavior.double_clicked", fake_double_clicked)

    dock = PlanscapeDockWidget()
    datalayer = DataLayer(id=10, name="Parcels", status="READY")
    item = model_item(datalayer)

    dock._handle_item_double_clicked(item, 0)

    assert calls == [datalayer]


def test_datalayer_double_click_adds_ready_layer(qgis_app, monkeypatch):
    assert qgis_app is not None

    calls = []

    monkeypatch.setattr("planscape.gui.behaviors.datalayer.add_datalayer_to_project", calls.append)

    dock = PlanscapeDockWidget()
    datalayer = DataLayer(id=10, name="Parcels", status="READY")

    behavior_for(datalayer).double_clicked(datalayer, dock._context(), model_item(datalayer))

    assert calls == [datalayer]


def test_datalayer_double_click_ignores_not_ready_layer(qgis_app, monkeypatch):
    assert qgis_app is not None

    calls = []

    monkeypatch.setattr("planscape.gui.behaviors.datalayer.add_datalayer_to_project", calls.append)

    dock = PlanscapeDockWidget()
    datalayer = DataLayer(id=10, name="Parcels", status="PENDING")

    behavior_for(datalayer).double_clicked(datalayer, dock._context(), model_item(datalayer))

    assert calls == []


def test_datalayer_double_click_ignores_missing_id(qgis_app, monkeypatch):
    assert qgis_app is not None

    calls = []

    monkeypatch.setattr("planscape.gui.behaviors.datalayer.add_datalayer_to_project", calls.append)

    dock = PlanscapeDockWidget()
    datalayer = DataLayer(name="Parcels", status="READY")

    behavior_for(datalayer).double_clicked(datalayer, dock._context(), model_item(datalayer))

    assert calls == []


def test_planscape_dock_dataset_collection_loads_workspace_datasets(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    def fake_list_workspace_datasets_request(base_url, authcfg_id, workspace_id):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["workspace_id"] = workspace_id
        return [Dataset(id=20, name="Base Data")]

    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.list_workspace_datasets_request",
        fake_list_workspace_datasets_request,
    )

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog", workspaces=[Workspace(id=7, name="Regional Plan")])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    datasets = workspace.child(0)

    dock._load_item_children(datasets)

    assert captured == {"base_url": "https://catalog.example", "authcfg_id": "authcfg-id", "workspace_id": 7}
    assert datasets.childCount() == 1
    assert datasets.child(0).text(0) == "Base Data"


def test_planscape_dock_style_collection_loads_workspace_styles(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    def fake_list_workspace_styles_request(base_url, authcfg_id, workspace_id):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["workspace_id"] = workspace_id
        return [Style(id=30, name="Default")]

    monkeypatch.setattr(
        "planscape.gui.behaviors.style_collection.list_workspace_styles_request",
        fake_list_workspace_styles_request,
    )

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog", workspaces=[Workspace(id=7, name="Regional Plan")])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    styles = workspace.child(1)

    dock._load_item_children(styles)

    assert captured == {"base_url": "https://catalog.example", "authcfg_id": "authcfg-id", "workspace_id": 7}
    assert styles.childCount() == 1
    assert styles.child(0).text(0) == "Default"


def test_planscape_dock_user_collection_loads_workspace_users(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    def fake_list_workspace_users_request(base_url, authcfg_id, workspace_id):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["workspace_id"] = workspace_id
        return [User(id=40, name="Regional Planner", email="planner@example.test")]

    monkeypatch.setattr(
        "planscape.gui.behaviors.user_collection.list_workspace_users_request",
        fake_list_workspace_users_request,
    )

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog", workspaces=[Workspace(id=7, name="Regional Plan")])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    users = workspace.child(2)

    dock._load_item_children(users)

    assert captured == {"base_url": "https://catalog.example", "authcfg_id": "authcfg-id", "workspace_id": 7}
    assert users.childCount() == 1
    assert users.child(0).text(0) == "Regional Planner"


def test_planscape_dock_collection_api_error_returns_empty_children(qgis_app, monkeypatch):
    assert qgis_app is not None

    def fake_list_workspace_datasets_request(base_url, authcfg_id, workspace_id):
        del base_url, authcfg_id, workspace_id
        message = "failed"
        raise WorkspaceAPIError(message)

    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.list_workspace_datasets_request",
        fake_list_workspace_datasets_request,
    )

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog", workspaces=[Workspace(id=7, name="Regional Plan")])
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace = dock.tree.topLevelItem(0).child(0)
    dock._load_item_children(workspace)
    datasets = workspace.child(0)

    dock._load_item_children(datasets)

    assert datasets.childCount() == 0


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

    def fake_list_workspaces_request(base_url: str, authcfg_id: str) -> list[Workspace]:
        del base_url, authcfg_id
        return [Workspace(id=8, name="Logged In Workspace")]

    monkeypatch.setattr("planscape.gui.planscape_dock.list_workspaces_request", fake_list_workspaces_request)

    dock = PlanscapeDockWidget()
    item = dock.tree.topLevelItem(0)

    dock._handle_item_clicked(item, 0)

    assert state["executed"] is True
    assert dock.tree.topLevelItem(0).text(0) == "Planscape (staging)"
    assert dock.tree.topLevelItem(0).childCount() == 1
    assert dock.tree.topLevelItem(0).child(0).text(0) == "Logged In Workspace"


def test_planscape_dock_server_context_menu_has_add_workspace_action(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(menu_action_label(action))

        def exec(self, position):
            del position

    monkeypatch.setattr("planscape.gui.planscape_dock.QMenu", FakeMenu)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    dock.show()
    root_rect = dock.tree.visualItemRect(dock.tree.topLevelItem(0))

    dock._show_context_menu(root_rect.center())

    assert captured["actions"] == ["Refresh", "<separator>", "Create new Workspace", "Login another env", "Logout"]


def test_planscape_dock_collection_context_menu_has_refresh_action(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(menu_action_label(action))

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

    assert captured["actions"] == ["Refresh", "<separator>", "New Dataset"]


def test_planscape_dock_workspace_context_menu_has_edit_action(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(menu_action_label(action))

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

    def item_at(position):
        del position
        return workspace

    monkeypatch.setattr(dock.tree, "itemAt", item_at)

    dock._show_context_menu(dock.tree.rect().center())

    assert captured["actions"] == ["Refresh", "<separator>", "Edit"]


def test_planscape_dock_add_workspace_opens_workspace_dialog(qgis_app, monkeypatch):
    assert qgis_app is not None

    state = {"executed": False}

    class FakeDialog:
        def __init__(self, parent=None):
            del parent

        def exec(self):
            state["executed"] = True

    monkeypatch.setattr("planscape.gui.commands.workspace.WorkspaceDialog", FakeDialog)

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog")
    item = dock._server_item(server)
    create_action = action_by_text(behavior_for(server).actions(server, dock._context(), item), "Create new Workspace")

    create_action.trigger()

    assert state["executed"] is True


def test_planscape_dock_add_workspace_creates_workspace_and_refreshes(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None):
            del parent

        def exec(self):
            return 1

        def workspace_name(self):
            return "New Workspace"

        def workspace_visibility(self):
            return "public"

    def fake_create_workspace_request(base_url, authcfg_id, request):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["request"] = request
        return Workspace(id=9, name="New Workspace", visibility=WorkspaceVisibility.PUBLIC)

    monkeypatch.setattr("planscape.gui.commands.workspace.WorkspaceDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.commands.workspace.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr("planscape.gui.commands.workspace.create_workspace_request", fake_create_workspace_request)

    def fake_list_workspaces_request(base_url: str, authcfg_id: str) -> list[Workspace]:
        del base_url, authcfg_id
        return [Workspace(id=9, name="New Workspace", visibility=WorkspaceVisibility.PUBLIC)]

    monkeypatch.setattr(
        "planscape.gui.planscape_dock.list_workspaces_request",
        fake_list_workspaces_request,
    )

    dock = PlanscapeDockWidget()
    server = Server(name="Planscape", env="catalog")
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(server))
    item = dock.tree.topLevelItem(0)
    create_action = action_by_text(behavior_for(server).actions(server, dock._context(), item), "Create new Workspace")

    create_action.trigger()

    assert captured["base_url"] == "https://catalog.example"
    assert captured["authcfg_id"] == "authcfg-id"
    assert captured["request"].to_dict() == {"name": "New Workspace", "visibility": "PUBLIC"}
    assert item.childCount() == 1
    assert item.child(0).text(0) == "New Workspace"


def test_planscape_dock_update_workspace_prefills_workspace_dialog(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None, *, workspace_id="", name="", visibility="private"):
            del parent
            captured["workspace_id"] = workspace_id
            captured["name"] = name
            captured["visibility"] = visibility

        def exec(self):
            return 0

    monkeypatch.setattr("planscape.gui.commands.workspace.WorkspaceDialog", FakeDialog)

    dock = PlanscapeDockWidget()
    workspace = Workspace(id=7, name="Regional Plan", visibility=WorkspaceVisibility.PUBLIC)
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(Server(workspaces=[workspace])))
    dock._load_item_children(dock.tree.topLevelItem(0))
    workspace_item = dock.tree.topLevelItem(0).child(0)

    edit_action = action_by_text(behavior_for(workspace).actions(workspace, dock._context(), workspace_item), "Edit")
    edit_action.trigger()

    assert captured == {"workspace_id": "7", "name": "Regional Plan", "visibility": "public"}


def test_planscape_dock_update_workspace_cancel_does_not_update(qgis_app, monkeypatch):
    assert qgis_app is not None

    state = {"update_called": False}

    class FakeDialog:
        def __init__(self, parent=None, *, workspace_id="", name="", visibility="private"):
            del parent, workspace_id, name, visibility

        def exec(self):
            return 0

    def fake_update_workspace_request(base_url, authcfg_id, workspace_id, request):
        del base_url, authcfg_id, workspace_id, request
        state["update_called"] = True
        return Workspace(id=7, name="Updated Plan")

    monkeypatch.setattr("planscape.gui.commands.workspace.WorkspaceDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.commands.workspace.update_workspace_request", fake_update_workspace_request)

    dock = PlanscapeDockWidget()
    workspace = Workspace(id=7, name="Regional Plan")
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(Server(workspaces=[workspace])))
    dock._load_item_children(dock.tree.topLevelItem(0))
    item = dock.tree.topLevelItem(0).child(0)

    edit_action = action_by_text(behavior_for(workspace).actions(workspace, dock._context(), item), "Edit")
    edit_action.trigger()

    assert state["update_called"] is False


def test_planscape_dock_update_workspace_updates_workspace_via_api(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None, *, workspace_id="", name="", visibility="private"):
            del parent, workspace_id, name, visibility

        def exec(self):
            return 1

        def workspace_name(self):
            return "Updated Plan"

        def workspace_visibility(self):
            return "private"

    def fake_update_workspace_request(base_url, authcfg_id, workspace_id, request):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["workspace_id"] = workspace_id
        captured["request"] = request
        return Workspace(id=7, name="Updated Plan", visibility=WorkspaceVisibility.PRIVATE)

    monkeypatch.setattr("planscape.gui.commands.workspace.WorkspaceDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.commands.workspace.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr("planscape.gui.commands.workspace.update_workspace_request", fake_update_workspace_request)

    dock = PlanscapeDockWidget()
    workspace = Workspace(id=7, name="Regional Plan", visibility=WorkspaceVisibility.PUBLIC)
    dock.tree.clear()
    dock.tree.addTopLevelItem(dock._server_item(Server(workspaces=[workspace])))
    dock._load_item_children(dock.tree.topLevelItem(0))
    item = dock.tree.topLevelItem(0).child(0)

    edit_action = action_by_text(behavior_for(workspace).actions(workspace, dock._context(), item), "Edit")
    edit_action.trigger()

    assert captured["base_url"] == "https://catalog.example"
    assert captured["authcfg_id"] == "authcfg-id"
    assert captured["workspace_id"] == 7
    assert captured["request"].to_dict() == {"name": "Updated Plan", "visibility": "PRIVATE"}
    assert item.text(0) == "Updated Plan"
    assert item.data(0, NODE_OBJECT_ROLE) == Workspace(
        id=7,
        name="Updated Plan",
        visibility=WorkspaceVisibility.PRIVATE,
    )


def test_planscape_dock_double_click_workspace_opens_workspace_dialog(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None, *, workspace_id="", name="", visibility="private"):
            del parent
            captured["workspace_id"] = workspace_id
            captured["name"] = name
            captured["visibility"] = visibility

        def exec(self):
            return 0

    monkeypatch.setattr("planscape.gui.commands.workspace.WorkspaceDialog", FakeDialog)

    dock = PlanscapeDockWidget()
    workspace = Workspace(id=7, name="Regional Plan", visibility=WorkspaceVisibility.PUBLIC)
    item = model_item(workspace)

    dock._handle_item_double_clicked(item, 0)

    assert captured == {"workspace_id": "7", "name": "Regional Plan", "visibility": "public"}


def test_planscape_dock_add_dataset_creates_dataset_and_refreshes(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None):
            del parent

        def exec(self):
            return 1

        def dataset_name(self):
            return "New Dataset"

        def dataset_visibility(self):
            return "public"

        def dataset_organization(self):
            return 3

        def dataset_version(self):
            return "2026.1"

        def dataset_modules(self):
            return ["forsys", "map"]

    def fake_create_dataset_request(base_url, authcfg_id, request):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["request"] = request
        return Dataset(id=21, name="New Dataset", visibility=WorkspaceVisibility.PUBLIC)

    def fake_list_workspace_datasets_request(base_url, authcfg_id, workspace_id):
        del base_url, authcfg_id, workspace_id
        return []

    monkeypatch.setattr("planscape.gui.commands.dataset.DatasetDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.commands.dataset.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr(
        "planscape.gui.commands.dataset.auth.get_base_url", lambda environment: f"https://{environment}.example"
    )
    monkeypatch.setattr("planscape.gui.commands.dataset.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.commands.dataset.create_dataset_request", fake_create_dataset_request)
    monkeypatch.setattr(
        "planscape.gui.behaviors.dataset_collection.list_workspace_datasets_request",
        fake_list_workspace_datasets_request,
    )

    dock = PlanscapeDockWidget()
    collection = DatasetCollection(workspace_id=7, count=0)
    item = model_item(collection)
    dock.tree.clear()
    dock.tree.addTopLevelItem(item)
    create_action = action_by_text(behavior_for(collection).actions(collection, dock._context(), item), "New Dataset")

    create_action.trigger()

    assert captured["base_url"] == "https://catalog.example"
    assert captured["authcfg_id"] == "authcfg-id"
    assert captured["request"].to_dict() == {
        "workspace_id": 7,
        "name": "New Dataset",
        "visibility": "PUBLIC",
        "modules": ["forsys", "map"],
        "organization": 3,
        "version": "2026.1",
    }
    assert item.childCount() == 1
    assert item.child(0).text(0) == "New Dataset"
    assert item.text(0) == "Datasets (1)"
    assert item.data(0, NODE_OBJECT_ROLE).count == 1


def test_planscape_dock_update_dataset_prefills_dataset_dialog(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None, *, dataset_id="", name="", visibility="private", modules=None):
            del parent
            captured["dataset_id"] = dataset_id
            captured["name"] = name
            captured["visibility"] = visibility
            captured["modules"] = modules

        def exec(self):
            return 0

    monkeypatch.setattr("planscape.gui.commands.dataset.DatasetDialog", FakeDialog)

    dock = PlanscapeDockWidget()
    dataset = Dataset(id=20, name="Base Data", visibility=WorkspaceVisibility.PUBLIC, modules=["map", "forsys"])
    item = model_item(dataset)

    edit_action = action_by_text(behavior_for(dataset).actions(dataset, dock._context(), item), "Edit")
    edit_action.trigger()

    assert captured == {
        "dataset_id": "20",
        "name": "Base Data",
        "visibility": "public",
        "modules": ["map", "forsys"],
    }


def test_planscape_dock_update_dataset_updates_dataset_via_api(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None, *, dataset_id="", name="", visibility="private", modules=None):
            del parent, dataset_id, name, visibility, modules

        def exec(self):
            return 1

        def dataset_name(self):
            return "Updated Data"

        def dataset_visibility(self):
            return "private"

        def dataset_modules(self):
            return ["map", "prioritize_sub_units"]

    def fake_update_dataset_request(base_url, authcfg_id, dataset_id, request):
        captured["base_url"] = base_url
        captured["authcfg_id"] = authcfg_id
        captured["dataset_id"] = dataset_id
        captured["request"] = request
        return Dataset(
            id=20,
            name="Updated Data",
            visibility=WorkspaceVisibility.PRIVATE,
            modules=["map", "prioritize_sub_units"],
        )

    monkeypatch.setattr("planscape.gui.commands.dataset.DatasetDialog", FakeDialog)
    monkeypatch.setattr("planscape.gui.commands.dataset.auth.get_environment", lambda: "catalog")
    monkeypatch.setattr(
        "planscape.gui.commands.dataset.auth.get_base_url", lambda environment: f"https://{environment}.example"
    )
    monkeypatch.setattr("planscape.gui.commands.dataset.auth.ensure_authenticated", lambda: "authcfg-id")
    monkeypatch.setattr("planscape.gui.commands.dataset.update_dataset_request", fake_update_dataset_request)

    dock = PlanscapeDockWidget()
    dataset = Dataset(id=20, name="Base Data", visibility=WorkspaceVisibility.PUBLIC)
    item = model_item(dataset)

    edit_action = action_by_text(behavior_for(dataset).actions(dataset, dock._context(), item), "Edit")
    edit_action.trigger()

    assert captured["base_url"] == "https://catalog.example"
    assert captured["authcfg_id"] == "authcfg-id"
    assert captured["dataset_id"] == 20
    assert captured["request"].to_dict() == {
        "name": "Updated Data",
        "visibility": "PRIVATE",
        "modules": ["map", "prioritize_sub_units"],
    }
    assert item.text(0) == "Updated Data"
    assert item.data(0, NODE_OBJECT_ROLE) == Dataset(
        id=20,
        name="Updated Data",
        visibility=WorkspaceVisibility.PRIVATE,
        modules=["map", "prioritize_sub_units"],
    )


def test_planscape_dock_double_click_dataset_opens_dataset_dialog(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {}

    class FakeDialog:
        def __init__(self, parent=None, *, dataset_id="", name="", visibility="private", modules=None):
            del parent
            captured["dataset_id"] = dataset_id
            captured["name"] = name
            captured["visibility"] = visibility
            captured["modules"] = modules

        def exec(self):
            return 0

    monkeypatch.setattr("planscape.gui.commands.dataset.DatasetDialog", FakeDialog)

    dock = PlanscapeDockWidget()
    dataset = Dataset(id=20, name="Base Data", visibility=WorkspaceVisibility.PUBLIC, modules=["map"])
    item = model_item(dataset)

    dock._handle_item_double_clicked(item, 0)

    assert captured == {"dataset_id": "20", "name": "Base Data", "visibility": "public", "modules": ["map"]}


def test_planscape_dock_root_context_menu_has_auth_actions_in_order(qgis_app, monkeypatch):
    assert qgis_app is not None

    captured = {"actions": []}

    class FakeMenu:
        def __init__(self, parent=None):
            del parent

        def addAction(self, action):
            captured["actions"].append(menu_action_label(action))

        def exec(self, position):
            del position

    monkeypatch.setattr("planscape.gui.planscape_dock.QMenu", FakeMenu)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.is_authenticated", lambda: True)
    monkeypatch.setattr("planscape.gui.planscape_dock.auth.get_environment", lambda: "catalog")

    dock = PlanscapeDockWidget()
    dock.show()
    root_rect = dock.tree.visualItemRect(dock.tree.topLevelItem(0))

    dock._show_context_menu(root_rect.center())

    assert captured["actions"] == ["Refresh", "<separator>", "Create new Workspace", "Login another env", "Logout"]


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
