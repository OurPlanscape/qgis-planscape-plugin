from planscape.gui.dataset_dialog import DatasetDialog


def test_dataset_dialog_defaults(qgis_app):
    assert qgis_app is not None

    dialog = DatasetDialog()

    assert dialog.windowTitle() == "create/edit dataset"
    assert dialog.dataset_id() == ""
    assert dialog.id_input.isReadOnly() is True
    assert dialog.name_input.text() == ""
    assert [dialog.visibility_combo.itemText(i) for i in range(dialog.visibility_combo.count())] == [
        "public",
        "private",
    ]
    assert dialog.visibility_combo.currentText() == "private"
    assert dialog.dataset_organization() is None
    assert dialog.dataset_version() is None
    assert dialog.dataset_modules() == "forsys,map,prioritize_sub_units"
    assert dialog.save_button.text() == "Save"
    assert dialog.focusWidget() == dialog.name_input


def test_dataset_dialog_supports_initial_values(qgis_app):
    assert qgis_app is not None

    dialog = DatasetDialog(
        dataset_id="dataset-123",
        name="Base Data",
        visibility="public",
        organization=3,
        version="2026.1",
        modules="forsys,map",
    )

    assert dialog.dataset_id() == "dataset-123"
    assert dialog.dataset_name() == "Base Data"
    assert dialog.dataset_visibility() == "public"
    assert dialog.dataset_organization() == 3
    assert dialog.dataset_version() == "2026.1"
    assert dialog.dataset_modules() == "forsys,map"
