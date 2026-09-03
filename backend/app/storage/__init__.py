import hashlib
import os
import re
import shutil
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Union

from app.config import get_settings


class StorageBackend:
    async def save(self, key: str, data: bytes, mime_type: str) -> str:
        raise NotImplementedError

    async def read(self, key: str) -> bytes:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    def generate_key(self, filename: str, prefix: str = "") -> str:
        raise NotImplementedError

    def public_url(self, key: str) -> str:
        raise NotImplementedError


def _safe_key_part(value: str) -> str:
    value = os.path.basename(value or "")
    value = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    return value


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.public_base = settings.API_URL.rstrip("/")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        safe = _safe_key_part(key)
        return self.base_path / safe

    async def save(self, key: str, data: bytes, mime_type: str) -> str:
        path = self._resolve(key)
        if path.parent != self.base_path:
            path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return key

    async def read(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(key)
        with open(path, "rb") as f:
            return f.read()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def generate_key(self, filename: str, prefix: str = "") -> str:
        safe_name = _safe_key_part(filename)
        digest = hashlib.sha1(safe_name.encode("utf-8")).hexdigest()[:12]
        components = [p for p in [prefix, f"{digest}_{safe_name}"] if p]
        key = "/".join(components).replace("\\", "/")
        return _safe_key_part(key) if prefix == "" else key

    def public_url(self, key: str) -> str:
        key = key.replace("\\", "/")
        return f"{self.public_base}/storage/{key}"


@lru_cache
def get_storage_backend() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        return LocalStorageBackend()
    return LocalStorageBackend(settings.STORAGE_PATH)
