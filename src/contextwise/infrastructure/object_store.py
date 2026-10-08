"""Content-addressed local storage for original upload bytes."""

import hashlib
import os
import tempfile
from pathlib import Path


class LocalObjectStore:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def put(self, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        directory = self.root / digest[:2]
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / digest
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == digest:
            return digest
        descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=".upload-")
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return digest

    def get(self, digest: str) -> bytes:
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("invalid object key")
        data = (self.root / digest[:2] / digest).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("object checksum mismatch")
        return data
