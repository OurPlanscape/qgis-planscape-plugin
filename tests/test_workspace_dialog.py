from planscape.gui.workspace_dialog import WorkspaceDialog


def test_workspace_dialog_defaults(qgis_app):
    assert qgis_app is not None

    dialog = WorkspaceDialog()

    assert dialog.windowTitle() == "create/edit workspace"
    assert dialog.workspace_id() == ""
    assert dialog.id_input.isReadOnly() is True
    assert dialog.name_input.text() == ""
    assert [dialog.visibility_combo.itemText(i) for i in range(dialog.visibility_combo.count())] == [
        "public",
        "private",
    ]
    assert dialog.visibility_combo.currentText() == "private"
    assert dialog.save_button.text() == "Save"


def test_workspace_dialog_supports_initial_values(qgis_app):
    assert qgis_app is not None

    dialog = WorkspaceDialog(workspace_id="workspace-123", name="Regional Plan", visibility="public")

    assert dialog.workspace_id() == "workspace-123"
    assert dialog.workspace_name() == "Regional Plan"
    assert dialog.workspace_visibility() == "public"
