from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, file_data: bytes, destination: str) -> str:
        """Upload file and return URL/path."""

    @abstractmethod
    async def download(self, source: str) -> bytes:
        """Download file and return bytes."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file."""

    @abstractmethod
    async def get_signed_url(self, path: str, expires_in: int = 900) -> str:
        """Generate time-limited access URL (15 min default)."""
