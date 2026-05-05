import pytest

from planscape.models.api.dataset import BrowseDatasetResponse, DatasetPayloadError
from planscape.models.domain import DataLayer


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
