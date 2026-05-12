import pytest

from planscape.api.exceptions import DatasetPayloadError
from planscape.models.api.dataset import (
    BrowseDatasetResponse,
    CreateDatasetRequest,
    DatasetResponse,
    UpdateDatasetRequest,
)
from planscape.models.domain import DataLayer, Dataset, WorkspaceVisibility


def test_create_dataset_request_serializes_payload():
    request = CreateDatasetRequest(workspace_id=7, name="Base Data", visibility=WorkspaceVisibility.PUBLIC)

    assert request.to_dict() == {
        "workspace_id": 7,
        "name": "Base Data",
        "visibility": "PUBLIC",
        "modules": ["forsys", "map", "prioritize_sub_units"],
    }


def test_create_dataset_request_serializes_optional_payload():
    request = CreateDatasetRequest(
        workspace_id=7,
        name="Base Data",
        organization=3,
        version="2026.1",
        modules="forsys, map",
    )

    assert request.to_dict() == {
        "workspace_id": 7,
        "name": "Base Data",
        "visibility": "PRIVATE",
        "modules": ["forsys", "map"],
        "organization": 3,
        "version": "2026.1",
    }


def test_update_dataset_request_omits_none_fields():
    request = UpdateDatasetRequest(name="Updated Data")

    assert request.to_dict() == {"name": "Updated Data"}


def test_dataset_response_to_domain_preserves_visibility():
    response = DatasetResponse.from_dict(
        {"id": 20, "name": "Base Data", "visibility": "PUBLIC", "modules": ["forsys", "map"]}
    )

    assert response.to_domain() == Dataset(
        id=20,
        name="Base Data",
        visibility=WorkspaceVisibility.PUBLIC,
        modules=["forsys", "map"],
    )


def test_dataset_response_uses_empty_modules_when_missing():
    response = DatasetResponse.from_dict({"id": 20, "name": "Base Data", "visibility": "PUBLIC"})

    assert response.to_domain().modules == []


def test_browse_dataset_response_parses_raw_list():
    response = BrowseDatasetResponse.from_list(
        [
            {
                "id": 1531,
                "name": "Potential Total Smoke Production Index",
                "path": ["Air Quality", "Particulate Matter"],
                "type": "RASTER",
                "map_url": None,
                "geometry_type": "RASTER",
                "status": "READY",
                "storage_type": "FILE_SYSTEM",
                "map_service_type": "COG",
                "info": {"crs": "EPSG:3857"},
                "metadata": {"modules": {"map": {"enabled": True}}},
                "styles": [{"id": 173}],
            }
        ]
    )

    assert response.datalayers == [
        DataLayer(
            id=1531,
            name="Potential Total Smoke Production Index",
            path=["Air Quality", "Particulate Matter"],
            type="RASTER",
            geometry_type="RASTER",
            status="READY",
            storage_type="FILE_SYSTEM",
            map_service_type="COG",
            info={"crs": "EPSG:3857"},
            metadata={"modules": {"map": {"enabled": True}}},
            styles=[{"id": 173}],
        )
    ]


def test_browse_dataset_response_rejects_paginated_shape():
    with pytest.raises(DatasetPayloadError, match="must be a list"):
        BrowseDatasetResponse.from_list({"count": 1, "results": []})  # type: ignore[arg-type]


def test_browse_dataset_response_rejects_invalid_path():
    with pytest.raises(DatasetPayloadError, match="path must be a list of strings"):
        BrowseDatasetResponse.from_list([{"id": 1531, "name": "Layer", "path": "Air Quality", "type": "RASTER"}])


def test_browse_dataset_response_builds_nested_category_tree():
    tree = BrowseDatasetResponse.from_list(
        [
            {"id": 1, "name": "Layer A1", "path": ["Category A"], "type": "RASTER"},
            {"id": 2, "name": "Layer B1", "path": ["Category B"], "type": "RASTER"},
            {"id": 3, "name": "Layer B1A", "path": ["Category B", "Category B1"], "type": "VECTOR"},
            {"id": 4, "name": "Root Layer", "path": [], "type": "RASTER"},
        ]
    ).to_tree()

    assert [category.name for category in tree.categories] == ["Category A", "Category B"]
    assert [layer.name for layer in tree.categories[0].datalayers] == ["Layer A1"]
    assert [layer.name for layer in tree.categories[1].datalayers] == ["Layer B1"]
    assert [category.name for category in tree.categories[1].categories] == ["Category B1"]
    assert [layer.name for layer in tree.categories[1].categories[0].datalayers] == ["Layer B1A"]
    assert [layer.name for layer in tree.datalayers] == ["Root Layer"]
