from __future__ import annotations

from typing import TYPE_CHECKING

from planscape import auth
from planscape.api.workspace import WorkspaceApiError, list_workspace_styles_request
from planscape.gui.behaviors.base import DockContext, DockNodeBehavior, action, noop, refresh_action
from planscape.models.domain import Model, StyleCollection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qgis.PyQt.QtWidgets import QAction, QTreeWidgetItem


class StyleCollectionBehavior(DockNodeBehavior):
    has_children = True

    def load_children(self, model: Model, context: DockContext) -> Sequence[Model]:  # noqa: ARG002
        if not isinstance(model, StyleCollection):
            return []
        if model.workspace_id is None:
            return []
        try:
            return list_workspace_styles_request(
                auth.get_base_url(auth.get_environment()),
                auth.ensure_authenticated(),
                model.workspace_id,
            )
        except WorkspaceApiError:
            return []

    def actions(self, model: Model, context: DockContext, item: QTreeWidgetItem) -> list[QAction]:  # noqa: ARG002
        return [action("New Style", context, noop), refresh_action(context, item)]
