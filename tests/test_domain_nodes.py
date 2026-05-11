from planscape.models.domain import (
    Category,
    CategoryCollection,
    DataLayer,
    DataLayerCollection,
    Dataset,
    DatasetCollection,
    LoginNode,
    Module,
    ModuleCollection,
    NodeKind,
    Server,
    Style,
    StyleCollection,
    User,
    UserCollection,
    Workspace,
    WorkspaceVisibility,
)


def test_domain_nodes_have_expected_kinds():
    assert LoginNode().kind == NodeKind.LOGIN
    assert Server().kind == NodeKind.SERVER
    assert Workspace().kind == NodeKind.WORKSPACE
    assert DatasetCollection().kind == NodeKind.DATASET_COLLECTION
    assert Dataset().kind == NodeKind.DATASET
    assert ModuleCollection().kind == NodeKind.MODULE_COLLECTION
    assert Module().kind == NodeKind.MODULE
    assert StyleCollection().kind == NodeKind.STYLE_COLLECTION
    assert Style().kind == NodeKind.STYLE
    assert DataLayerCollection().kind == NodeKind.DATALAYER_COLLECTION
    assert DataLayer().kind == NodeKind.DATALAYER
    assert UserCollection().kind == NodeKind.USER_COLLECTION
    assert User().kind == NodeKind.USER
    assert CategoryCollection().kind == NodeKind.CATEGORY_COLLECTION
    assert Category().kind == NodeKind.CATEGORY


def test_domain_nodes_provide_default_node_labels():
    assert Workspace(name="Regional Plan").node_label() == "Regional Plan"
    assert Dataset(name="Base Data").node_label() == "Base Data"
    assert Server(name="Planscape", env="catalog").node_label() == "Planscape (catalog)"
    assert LoginNode().node_label() == "Click to login"
    assert DatasetCollection(workspace_id=10).node_label() == "Datasets"
    assert DatasetCollection(workspace_id=10).node_key() == "dataset_collection:workspace:10"
    assert ModuleCollection(dataset_id=20).node_label() == "Modules"
    assert ModuleCollection(dataset_id=20).node_key() == "module_collection:dataset:20"
    assert DataLayerCollection(dataset_id=20).node_key() == "datalayer_collection:dataset:20"


def test_child_collections_default_to_empty_lists():
    server = Server()
    workspace = Workspace()
    dataset = Dataset()

    assert server.workspaces == []
    assert workspace.datasets == []
    assert workspace.styles == []
    assert workspace.users == []
    assert dataset.datalayers == []
    assert dataset.categories == []
    assert dataset.modules == []


def test_child_collections_are_not_shared_between_instances():
    first_server = Server()
    second_server = Server()

    first_server.workspaces.append(Workspace(name="Regional Plan"))

    assert len(first_server.workspaces) == 1
    assert second_server.workspaces == []


def test_domain_nodes_represent_dock_tree_relationships():
    datalayer = DataLayer(id=30, name="Roads")
    category = Category(id=40, name="Transportation")
    dataset = Dataset(id=20, name="Base Data", datalayers=[datalayer], categories=[category])
    style = Style(id=50, name="Default")
    user = User(id=60, name="Planner", email="planner@example.com")
    workspace = Workspace(
        id=10,
        name="Regional Plan",
        visibility=WorkspaceVisibility.PUBLIC,
        datasets=[dataset],
        styles=[style],
        users=[user],
    )
    server = Server(name="Planscape", workspaces=[workspace])

    assert server.workspaces == [workspace]
    assert server.workspaces[0].datasets == [dataset]
    assert server.workspaces[0].styles == [style]
    assert server.workspaces[0].users == [user]
    assert server.workspaces[0].datasets[0].datalayers == [datalayer]
    assert server.workspaces[0].datasets[0].categories == [category]
