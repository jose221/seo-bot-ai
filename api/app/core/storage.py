from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote, urlparse

import boto3
from botocore.client import Config

from app.core.config import settings


class PublicAssetStorage:
    def __init__(self) -> None:
        self.local_storage_path = Path(settings.STORAGE_PATH)
        self.local_url_prefix = settings.STORAGE_URL_PREFIX.rstrip("/")
        self.endpoint_url = self._normalize_optional_url(
            settings.HERANDRO_STORAGE_ENDPOINT_URL or settings.SEAWEED_ENDPOINT
        )
        self.access_key = self._normalize_optional_string(
            settings.HERANDRO_STORAGE_ACCESS_KEY or settings.SEAWEED_ACCESS_KEY
        )
        self.secret_key = self._normalize_optional_string(
            settings.HERANDRO_STORAGE_SECRET_KEY or settings.SEAWEED_SECRET_KEY
        )
        self.public_base_url = self._normalize_optional_url(
            settings.HERANDRO_STORAGE_PUBLIC_BASE_URL
        )
        self.public_bucket = settings.HERANDRO_STORAGE_PUBLIC_BUCKET.strip()
        self.public_folder = self._normalize_folder(settings.HERANDRO_STORAGE_PUBLIC_FOLDER)
        self.remote_enabled = bool(
            self.endpoint_url and self.public_bucket
        )
        self.s3_client = None

        if self.remote_enabled:
            client_kwargs = {
                "endpoint_url": self.endpoint_url,
                "config": Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
                "region_name": settings.HERANDRO_STORAGE_REGION_NAME,
            }
            if self.access_key:
                client_kwargs["aws_access_key_id"] = self.access_key
            if self.secret_key:
                client_kwargs["aws_secret_access_key"] = self.secret_key

            self.s3_client = boto3.client("s3", **client_kwargs)

    @staticmethod
    def _normalize_optional_string(value: Optional[str]) -> Optional[str]:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    @classmethod
    def _normalize_optional_url(cls, value: Optional[str]) -> Optional[str]:
        normalized = cls._normalize_optional_string(value)
        if not normalized:
            return None
        if normalized.startswith(("http://", "https://")):
            return normalized.rstrip("/")
        scheme = "https" if settings.HERANDRO_STORAGE_SECURE else "http"
        return f"{scheme}://{normalized.rstrip('/')}"

    @staticmethod
    def is_remote_url(value: Optional[str]) -> bool:
        if not value or not isinstance(value, str):
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        normalized = Path(filename or "").name.strip().replace("\\", "_").replace("/", "_")
        return normalized or "file"

    @classmethod
    def _normalize_folder(cls, folder: Optional[str]) -> str:
        if not folder:
            return ""
        parts: list[str] = []
        for raw_part in folder.replace("\\", "/").split("/"):
            part = raw_part.strip()
            if not part or part in {".", ".."}:
                continue
            parts.append(part)
        return "/".join(parts)

    @classmethod
    def _guess_content_type(cls, filename: str, provided: Optional[str] = None) -> str:
        if provided:
            return provided
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

    def uses_remote_storage(self) -> bool:
        return self.remote_enabled

    def _build_remote_object_name(self, *, folder: Optional[str], filename: str) -> str:
        parts: list[str] = []
        if self.public_folder:
            parts.append(self.public_folder)
        normalized_folder = self._normalize_folder(folder)
        if normalized_folder:
            parts.append(normalized_folder)
        parts.append(self._sanitize_filename(filename))
        return "/".join(parts)

    def _build_local_relative_path(self, *, folder: Optional[str], filename: str) -> str:
        normalized_folder = self._normalize_folder(folder)
        filename = self._sanitize_filename(filename)
        if normalized_folder:
            return f"{normalized_folder}/{filename}"
        return filename

    def upload_public_bytes(
        self,
        *,
        filename: str,
        data: bytes,
        folder: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> dict[str, Any]:
        resolved_name = self._sanitize_filename(filename)
        resolved_type = self._guess_content_type(resolved_name, content_type)

        if self.remote_enabled:
            object_name = self._build_remote_object_name(folder=folder, filename=resolved_name)
            assert self.s3_client is not None
            self.s3_client.put_object(
                Bucket=self.public_bucket,
                Key=object_name,
                Body=data,
                ContentType=resolved_type,
            )
            base_url = (self.public_base_url or self.endpoint_url or "").rstrip("/")
            return {
                "path": f"{self.public_bucket}/{object_name}",
                "url": f"{base_url}/{self.public_bucket}/{quote(object_name, safe='/')}",
                "content_type": resolved_type,
                "size": len(data),
            }

        relative_path = self._build_local_relative_path(folder=folder, filename=resolved_name)
        target_path = self.local_storage_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        return {
            "path": str(target_path),
            "url": f"{self.local_url_prefix}/{relative_path}",
            "content_type": resolved_type,
            "size": len(data),
        }

    def upload_public_file(
        self,
        local_path: Path,
        *,
        folder: Optional[str] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        remove_local: bool = False,
    ) -> dict[str, Any]:
        try:
            data = local_path.read_bytes()
            return self.upload_public_bytes(
                filename=filename or local_path.name,
                data=data,
                folder=folder,
                content_type=content_type,
            )
        finally:
            if remove_local:
                try:
                    if local_path.exists():
                        local_path.unlink()
                except OSError:
                    pass

    def upload_public_text(
        self,
        *,
        filename: str,
        content: str,
        folder: Optional[str] = None,
        content_type: str = "text/plain; charset=utf-8",
    ) -> dict[str, Any]:
        return self.upload_public_bytes(
            filename=filename,
            data=content.encode("utf-8"),
            folder=folder,
            content_type=content_type,
        )


_public_asset_storage: Optional[PublicAssetStorage] = None


def get_public_asset_storage() -> PublicAssetStorage:
    global _public_asset_storage
    if _public_asset_storage is None:
        _public_asset_storage = PublicAssetStorage()
    return _public_asset_storage
