from __future__ import annotations

from enum import StrEnum


class NodeKind(StrEnum):
    LOGIN = "login"
    SERVER = "server"
    WORKSPACE = "workspace"
    DATASET_COLLECTION = "dataset_collection"
    DATASET = "dataset"
    MODULE_COLLECTION = "module_collection"
    MODULE = "module"
    STYLE_COLLECTION = "style_collection"
    STYLE = "style"
    DATALAYER_COLLECTION = "datalayer_collection"
    DATALAYER = "datalayer"
    USER_COLLECTION = "user_collection"
    USER = "user"
    CATEGORY_COLLECTION = "category_collection"
    CATEGORY = "category"
