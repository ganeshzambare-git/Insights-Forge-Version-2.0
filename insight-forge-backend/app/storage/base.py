from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class SupportsAsyncRead(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


@dataclass(frozen=True)
class StoredObject:
    uri: str
    size_bytes: int


class StorageProvider(Protocol):
    async def save(self, *, tenant_id: UUID, dataset_id: UUID, filename: str, source: SupportsAsyncRead, max_bytes: int) -> StoredObject: ...
    async def delete(self, uri: str) -> None: ...
