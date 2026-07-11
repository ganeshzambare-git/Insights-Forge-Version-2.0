class StorageError(Exception):
    """Base storage failure."""


class FileTooLargeError(StorageError):
    """Raised when a streamed upload exceeds its configured limit."""
