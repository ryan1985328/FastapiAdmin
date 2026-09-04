"""安全的公共媒体读取与 URL 解析。

存储管理接口继续保持鉴权；本模块只提供按精确存储 key 读取商品等公开内容，
并把本地磁盘路径与对象存储 URL 的差异收敛在一个解析器里。
"""

from __future__ import annotations

import mimetypes
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from fastapi import Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from starlette.background import BackgroundTask

from app.api.v1.module_storage.core.base import StorageAdapterConfig
from app.api.v1.module_storage.core.constants import StorageProtocol
from app.api.v1.module_storage.core.encrypt import decrypt_password
from app.api.v1.module_storage.core.factory import StorageAdapterFactory
from app.api.v1.module_storage.source.service import StorageSourceService
from app.common.enums import RET
from app.config.setting import settings
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException

PUBLIC_MEDIA_ROUTE = "/storage/file/public"
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:($|/)")


def normalize_public_storage_key(value: str) -> str:
    """Return a canonical relative storage key or raise ``ValueError``.

    The value is decoded repeatedly so encoded traversal cannot bypass the
    check. Empty/dot components, absolute paths, URLs, NUL bytes and
    backslash-based paths are rejected instead of being normalized loosely.
    """

    if not isinstance(value, str) or not value.strip():
        raise ValueError("请提供文件路径")

    candidate = value
    for _ in range(3):
        decoded = unquote(candidate)
        if decoded == candidate:
            break
        candidate = decoded

    if "\x00" in candidate:
        raise ValueError("非法的文件路径")
    if "\\" in candidate:
        raise ValueError("非法的文件路径")

    parsed = urlparse(candidate)
    normalized = candidate
    if parsed.scheme or parsed.netloc:
        raise ValueError("非法的文件路径")
    if normalized.startswith("/") or normalized.startswith("//") or _WINDOWS_ABSOLUTE_PATH.match(normalized):
        raise ValueError("非法的文件路径")

    parts = normalized.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValueError("非法的文件路径")

    # ``Path`` is an additional platform-aware guard; the route itself never
    # accepts an absolute path even when the app runs on Windows.
    if Path(normalized).is_absolute():
        raise ValueError("非法的文件路径")
    return "/".join(parts)


def validate_public_storage_key(value: str) -> str:
    """Validate a key for storage operations and expose project exceptions."""

    try:
        return normalize_public_storage_key(value)
    except ValueError as exc:
        raise CustomException(msg=str(exc)) from exc


def public_media_path(remote_path: str, source_id: int | None = None) -> str:
    """Build the same-origin browser path for a validated storage key."""

    key = normalize_public_storage_key(remote_path)
    root = settings.ROOT_PATH.rstrip("/")
    path = f"{root}{PUBLIC_MEDIA_ROUTE}/{quote(key, safe='/')}"
    if source_id is not None:
        path = f"{path}?source_id={source_id}"
    return path or "/"


def public_media_url(request: Request, remote_path: str, source_id: int | None = None) -> str:
    """Build an absolute public URL without exposing the local storage root."""

    base = str(request.base_url).rstrip("/")
    root = settings.ROOT_PATH.rstrip("/")
    if root and base.endswith(root):
        base = base[: -len(root)].rstrip("/")
    return f"{base}{public_media_path(remote_path, source_id)}"


def is_browser_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _delete_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


class PublicMediaService:
    """Resolve a native storage reference for public read-only consumers."""

    def __init__(self, db) -> None:
        self.db = db

    async def _source_config(self, source_id: int | None) -> StorageAdapterConfig:
        source = await StorageSourceService(AuthSchema(), self.db).get_active_source(source_id)
        return StorageAdapterConfig(
            protocol=StorageProtocol(source.protocol),
            host=source.host,
            port=source.port,
            username=source.username,
            password=decrypt_password(source.password),
            bucket=source.bucket,
            endpoint=source.endpoint,
            region=source.region,
            path_prefix=source.path_prefix,
            is_secure=source.is_secure,
            implicit_tls=source.implicit_tls,
        )

    async def url_for(
        self,
        remote_path: str,
        source_id: int | None = None,
        request: Request | None = None,
    ) -> str:
        """Return a provider URL when available, otherwise the safe read route."""

        key = normalize_public_storage_key(remote_path)
        config = await self._source_config(source_id)
        adapter = StorageAdapterFactory.create(config)
        try:
            provider_url = await adapter.get_url(key)
        finally:
            await adapter.close()

        if is_browser_url(provider_url):
            return provider_url
        if request is not None:
            return public_media_url(request, key, source_id)
        return public_media_path(key, source_id)

    async def response(self, remote_path: str, source_id: int | None = None) -> Response:
        """Read exactly one public object, without directory/listing access."""

        try:
            key = normalize_public_storage_key(remote_path)
        except ValueError as exc:
            raise CustomException(msg="文件不存在", code=RET.NOT_FOUND.code, status_code=404) from exc
        config = await self._source_config(source_id)
        adapter = StorageAdapterFactory.create(config)

        if config.protocol == StorageProtocol.LOCAL:
            root = Path(config.host).expanduser().resolve()
            candidate = (root / key).resolve()
            if not candidate.is_relative_to(root):
                await adapter.close()
                raise CustomException(msg="文件不存在", code=RET.NOT_FOUND.code, status_code=404)

        try:
            provider_url = await adapter.get_url(key)
            if is_browser_url(provider_url):
                return RedirectResponse(provider_url)

            if not await adapter.exists(key):
                raise CustomException(msg="文件不存在", code=RET.NOT_FOUND.code, status_code=404)

            suffix = Path(key).suffix
            fd, local_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            try:
                await adapter.download(key, local_path)
            except Exception as exc:
                _delete_temp_file(local_path)
                raise CustomException(msg="文件不存在", code=RET.NOT_FOUND.code, status_code=404) from exc
        finally:
            await adapter.close()

        media_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        return FileResponse(
            local_path,
            media_type=media_type,
            filename=Path(key).name,
            headers={"Cache-Control": "public, max-age=300"},
            background=BackgroundTask(_delete_temp_file, local_path),
        )


__all__ = [
    "PUBLIC_MEDIA_ROUTE",
    "PublicMediaService",
    "is_browser_url",
    "normalize_public_storage_key",
    "public_media_path",
    "public_media_url",
    "validate_public_storage_key",
]
