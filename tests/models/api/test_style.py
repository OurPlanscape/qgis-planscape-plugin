import pytest

from planscape.api.exceptions import StylePayloadError
from planscape.models.api.style import CreateStyleRequest, StyleResponse
from planscape.models.domain import Style


def test_create_style_request_serializes_payload():
    request = CreateStyleRequest(
        name="Smoke Style",
        data={"map_type": "VALUES"},
        organization=3,
        datalayers=[20],
    )

    assert request.to_dict() == {
        "name": "Smoke Style",
        "type": "RASTER",
        "data": {"map_type": "VALUES"},
        "organization": 3,
        "datalayers": [20],
    }


def test_style_response_to_domain():
    assert StyleResponse.from_dict({"id": 30, "name": "Default"}).to_domain() == Style(id=30, name="Default")


def test_style_response_rejects_missing_id():
    with pytest.raises(StylePayloadError):
        StyleResponse.from_dict({"name": "Default"})
