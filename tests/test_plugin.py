from planscape.plugin import Plugin
from planscape.qgis_plugin_tools.tools.resources import plugin_name


def test_plugin_name():
    assert plugin_name() == "Planscape"


def test_plugin_run_opens_auth_dialog(monkeypatch):
    state = {"created": False, "executed": False}

    class FakeDialog:
        def __init__(self, parent=None):
            state["created"] = parent is not None

        def exec(self):
            state["executed"] = True

    monkeypatch.setattr("planscape.plugin.AuthDialog", FakeDialog)

    plugin = Plugin()

    plugin.run()

    assert state == {"created": True, "executed": True}
