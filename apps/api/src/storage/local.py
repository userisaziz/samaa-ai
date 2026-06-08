import os
from pathlib import Path

from src.config import settings
from src.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self):
        self.base_dir = Path(settings.local_upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file_data: bytes, destination: str) -> str:
        file_path = self.base_dir / destination
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_data)
        return str(file_path)

    async def download(self, source: str) -> bytes:
        file_path = self.base_dir / source
        return file_path.read_bytes()

    async def delete(self, path: str) -> None:
        file_path = self.base_dir / path
        if file_path.exists():
            file_path.unlink()

    async def get_signed_url(self, path: str, expires_in: int = 900) -> str:
        # Local storage doesn't have signed URLs — return the file path
        return str(self.base_dir / path)


def get_storage() -> StorageBackend:
    """Factory function to get the configured storage backend."""
    if settings.storage_backend == "local":
        return LocalStorage()
    # Future: add S3Storage()
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")
