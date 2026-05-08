import pytest

from planscape.api.exceptions import DataLayerPayloadError
from planscape.models.api.datalayer import DataLayerUrlsResponse


def test_datalayer_urls_response_parses_layer_url():
    response = DataLayerUrlsResponse.from_dict({"layer_url": "https://example.test/layer"})

    assert response.layer_url == "https://example.test/layer"


def test_datalayer_urls_response_rejects_missing_layer_url():
    with pytest.raises(DataLayerPayloadError, match="layer_url must be a string"):
        DataLayerUrlsResponse.from_dict({})


def test_datalayer_urls_response_rejects_non_string_layer_url():
    with pytest.raises(DataLayerPayloadError, match="layer_url must be a string"):
        DataLayerUrlsResponse.from_dict({"layer_url": None})
