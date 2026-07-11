from app.core.config import settings
from app.storage.local import LocalStorageProvider


def get_storage_provider() -> LocalStorageProvider:
    return LocalStorageProvider(settings.STORAGE_LOCAL_PATH)
