from __future__ import annotations

import json
from typing import ClassVar

import pytest
from qgis.PyQt.QtCore import QByteArray
from qgis.PyQt.QtNetwork import QNetworkReply

from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginNetworkException
from planscape.tools import network


class FakeQUrl:
    def __init__(self, url: str) -> None:
        self.url = url


class FakeQNetworkRequest:
    def __init__(self, url: FakeQUrl) -> None:
        self.url = url
        self.headers: dict[bytes, bytes] = {}

    def setRawHeader(self, key: bytes, value: bytes) -> None:
        self.headers[key] = value


class FakeReply:
    def __init__(
        self,
        content: bytes,
        error: QNetworkReply.NetworkError = QNetworkReply.NetworkError.NoError,
        error_string: str = "",
        default_name: str = "",
    ) -> None:
        self._content = content
        self._error = error
        self._error_string = error_string
        self._default_name = default_name

    def error(self) -> QNetworkReply.NetworkError:
        return self._error

    def content(self) -> bytes:
        return self._content

    def errorString(self) -> str:
        return self._error_string

    def hasRawHeader(self, header: QByteArray) -> bool:
        return bool(self._default_name) and bytes(header) == bytes(network.CONTENT_DISPOSITION_BYTE_HEADER)

    def rawHeader(self, header: QByteArray) -> QByteArray:
        del header
        return QByteArray(bytes(f'attachment; filename="{self._default_name}"', network.ENCODING))


class FakeBlockingNetworkRequest:
    instances: ClassVar[list[FakeBlockingNetworkRequest]] = []
    next_reply: ClassVar[FakeReply] = FakeReply(b"{}")

    def __init__(self) -> None:
        self.authcfg_id = ""
        self.request = None
        self.byte_data = b""
        self.instances.append(self)

    def setAuthCfg(self, authcfg_id: str) -> None:
        self.authcfg_id = authcfg_id

    def put(self, request: FakeQNetworkRequest, byte_data: bytes) -> None:
        self.request = request
        self.byte_data = byte_data

    def reply(self) -> FakeReply:
        return self.next_reply


@pytest.fixture(autouse=True)
def fake_qgis_network(monkeypatch):
    FakeBlockingNetworkRequest.instances = []
    FakeBlockingNetworkRequest.next_reply = FakeReply(b"{}")
    monkeypatch.setattr(network, "QUrl", FakeQUrl)
    monkeypatch.setattr(network, "QNetworkRequest", FakeQNetworkRequest)
    monkeypatch.setattr(network, "QgsBlockingNetworkRequest", FakeBlockingNetworkRequest)
    monkeypatch.setattr(network, "_user_agent", lambda: "PlanscapeTestAgent")


def test_put_decodes_response(monkeypatch):
    def fake_put_raw(url: str, encoding: str, authcfg_id: str, data: dict[str, object] | None) -> tuple[bytes, str]:
        assert url == "https://example.test/workspaces/1/"
        assert encoding == "utf-8"
        assert authcfg_id == "authcfg-id"
        assert data == {"name": "Updated"}
        return b'{"id": 1}', ""

    monkeypatch.setattr(network, "put_raw", fake_put_raw)

    response = network.put("https://example.test/workspaces/1/", authcfg_id="authcfg-id", data={"name": "Updated"})

    assert response == '{"id": 1}'


def test_put_raw_sends_json_put_request_with_authcfg():
    FakeBlockingNetworkRequest.next_reply = FakeReply(b'{"id": 1}', default_name="workspace.json")

    content, default_name = network.put_raw(
        "https://example.test/workspaces/1/",
        authcfg_id="authcfg-id",
        data={"name": "Updated", "visibility": "PUBLIC"},
    )

    blocking_request = FakeBlockingNetworkRequest.instances[0]
    assert content == b'{"id": 1}'
    assert default_name == "workspace.json"
    assert blocking_request.authcfg_id == "authcfg-id"
    assert blocking_request.request.url.url == "https://example.test/workspaces/1/"
    assert blocking_request.request.headers[b"User-Agent"] == b"PlanscapeTestAgent"
    assert blocking_request.request.headers[b"Content-Type"] == b"application/json; charset=utf-8"
    assert json.loads(blocking_request.byte_data.decode("utf-8")) == {
        "name": "Updated",
        "visibility": "PUBLIC",
    }


def test_put_raw_sends_empty_json_object_without_data():
    network.put_raw("https://example.test/workspaces/1/")

    blocking_request = FakeBlockingNetworkRequest.instances[0]
    assert json.loads(blocking_request.byte_data.decode("utf-8")) == {}
    assert blocking_request.authcfg_id == ""


def test_put_raw_raises_network_exception_on_reply_error(monkeypatch):
    monkeypatch.setattr(network, "bar_msg", lambda message: {"message": message})
    FakeBlockingNetworkRequest.next_reply = FakeReply(
        b"upstream failed",
        error=QNetworkReply.NetworkError.ConnectionRefusedError,
        error_string="Connection refused",
    )

    with pytest.raises(QgsPluginNetworkException, match="upstream failed") as exc_info:
        network.put_raw("https://example.test/workspaces/1/", data={"name": "Updated"})

    assert exc_info.value.error == QNetworkReply.NetworkError.ConnectionRefusedError
    assert exc_info.value.bar_msg == {"message": "Connection refused"}
