"""Tickets revogáveis em disco, compartilhados pelos workers da mesma VM."""

from __future__ import annotations

import os
import re
import secrets
import time
from pathlib import Path


class SessionTickets:
    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def create(self, lifetime_seconds: float) -> str:
        self.prune()
        identifier = secrets.token_urlsafe(32)
        path = self.directory / f"{identifier}.session"
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="ascii") as stream:
            stream.write(str(time.time() + lifetime_seconds))
        return identifier

    def valid(self, identifier: object) -> bool:
        path = self._path(identifier)
        if path is None:
            return False
        try:
            expires = float(path.read_text(encoding="ascii"))
            if time.time() < expires:
                return True
            path.unlink(missing_ok=True)
        except (OSError, ValueError):
            pass
        return False

    def revoke(self, identifier: object) -> None:
        path = self._path(identifier)
        if path is not None:
            path.unlink(missing_ok=True)

    def prune(self) -> None:
        for path in self.directory.glob("*.session"):
            self.valid(path.stem)

    def _path(self, identifier: object) -> Path | None:
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", identifier):
            return None
        return self.directory / f"{identifier}.session"
