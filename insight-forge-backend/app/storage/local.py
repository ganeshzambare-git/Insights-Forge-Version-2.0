from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.storage.base import StoredObject, SupportsAsyncRead
from app.storage.exceptions import FileTooLargeError, StorageError


class LocalStorageProvider:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    async def save(self, *, tenant_id: UUID, dataset_id: UUID, filename: str, source: SupportsAsyncRead, max_bytes: int) -> StoredObject:
        safe_name = Path(filename).name
        target = (self.root / str(tenant_id) / f"{dataset_id}_{safe_name}").resolve()
        if self.root not in target.parents:
            raise StorageError("Unsafe upload filename")
        target.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        try:
            with target.open("wb") as handle:
                while chunk := await source.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        handle.close()
                        target.unlink(missing_ok=True)
                        raise FileTooLargeError(f"Upload exceeds {max_bytes} bytes")
                    handle.write(chunk)
        except OSError as exc:
            raise StorageError(str(exc)) from exc
        return StoredObject(uri=str(target), size_bytes=size)

    async def delete(self, uri: str) -> None:
        path = Path(uri).resolve()
        if self.root in path.parents:
            path.unlink(missing_ok=True)
