from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from qgis.PyQt.QtWidgets import QAction, QTreeWidget, QTreeWidgetItem, QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from planscape.models.domain import Model


@dataclass(frozen=True)
class DockContext:
    tree: QTreeWidget
    parent: QWidget
    refresh_node: Callable[[QTreeWidgetItem], None]
    create_workspace: Callable[[], None]
    login_another_env: Callable[[], None]
    logout: Callable[[], None]


class DockNodeBehavior:
    has_children = False

    def load_children(self, model: Model, context: DockContext) -> List[Model]:  # noqa: ARG002
        return []

    def actions(
        self,
        model: Model,  # noqa: ARG002
        context: DockContext,  # noqa: ARG002
        item: QTreeWidgetItem,  # noqa: ARG002
    ) -> List[QAction]:
        return []


def action(text: str, context: DockContext, callback: Callable[[], None]) -> QAction:
    qaction = QAction(text, context.tree)
    qaction.triggered.connect(callback)
    return qaction


def refresh_action(context: DockContext, item: QTreeWidgetItem) -> QAction:
    qaction = QAction("Refresh", context.tree)
    qaction.triggered.connect(lambda: context.refresh_node(item))
    return qaction


def noop() -> None:
    return None
