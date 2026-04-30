from __future__ import annotations

import json
import logging
from typing import Any

from qgis.core import Qgis, QgsBlockingNetworkRequest, QgsNetworkReplyContent
from qgis.PyQt.QtCore import QByteArray, QSettings, QUrl
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest

from planscape.qgis_plugin_tools.tools.custom_logging import bar_msg
from planscape.qgis_plugin_tools.tools.exceptions import QgsPluginNetworkException
from planscape.qgis_plugin_tools.tools.resources import plugin_name

logger = logging.getLogger(__name__)
ENCODING = "utf-8"
CONTENT_DISPOSITION_HEADER = "Content-Disposition"
CONTENT_DISPOSITION_BYTE_HEADER = QByteArray(bytes(CONTENT_DISPOSITION_HEADER, ENCODING))


def put(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    data: dict[str, Any] | None = None,
) -> str:
    content, _ = put_raw(url, encoding, authcfg_id, data)
    return content.decode(encoding)


def put_raw(
    url: str,
    encoding: str = ENCODING,
    authcfg_id: str = "",
    data: dict[str, Any] | None = None,
) -> tuple[bytes, str]:
    logger.debug(url)
    request = QNetworkRequest(QUrl(url))
    request.setRawHeader(b"User-Agent", bytes(_user_agent(), encoding))
    request.setRawHeader(b"Content-Type", bytes(f"application/json; charset={encoding}", encoding))

    request_blocking = QgsBlockingNetworkRequest()
    if authcfg_id:
        request_blocking.setAuthCfg(authcfg_id)

    byte_data = bytes(json.dumps(data or {}), encoding)
    request_blocking.put(request, byte_data)

    reply: QgsNetworkReplyContent = request_blocking.reply()
    reply_error = reply.error()
    if reply_error != QNetworkReply.NetworkError.NoError:
        message = bytes(reply.content()).decode(encoding) if bytes(reply.content()) else None
        raise QgsPluginNetworkException(
            message=message,
            error=reply_error,
            bar_msg=bar_msg(reply.errorString()),
        )

    return bytes(reply.content()), _default_name(reply, encoding)


def _user_agent() -> str:
    user_agent = QSettings().value("/qgis/networkAndProxy/userAgent", "Mozilla/5.0")
    user_agent += " " if len(user_agent) else ""
    return f"{user_agent}QGIS/{Qgis.QGIS_VERSION_INT} {plugin_name()}"


def _default_name(reply: QgsNetworkReplyContent, encoding: str) -> str:
    if not reply.hasRawHeader(CONTENT_DISPOSITION_BYTE_HEADER):
        return ""

    header: QByteArray = reply.rawHeader(CONTENT_DISPOSITION_BYTE_HEADER)
    default_name = bytes(header).decode(encoding).split("filename=")[1]
    if default_name[0] in ['"', "'"]:
        return default_name[1:-1]
    return default_name
