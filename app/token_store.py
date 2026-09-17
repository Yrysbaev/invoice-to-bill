"""Persist OAuth tokens to a local JSON file.

Milestone 2: a deliberately simple, single-company token store. It keeps the
access token, refresh token, the QuickBooks realm (company) id, and absolute
expiry timestamps so callers can tell when a refresh is due.

This is fine for a local, single-user tool. A multi-user or hosted app would
store tokens per-user in a database instead.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class TokenBundle:
    access_token: str
    refresh_token: str
    realm_id: str
    # Absolute unix timestamps (seconds) when each token expires.
    access_expires_at: float
    refresh_expires_at: float

    def access_expired(self, leeway_seconds: int = 60) -> bool:
        """True if the access token is expired (or about to be)."""
        return time.time() >= (self.access_expires_at - leeway_seconds)

    def refresh_expired(self) -> bool:
        return time.time() >= self.refresh_expires_at


class TokenStore:
    """Reads and writes a single :class:`TokenBundle` to a JSON file."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> Optional[TokenBundle]:
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return TokenBundle(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # Corrupt or partial file — treat as "not connected".
            return None

    def save(self, bundle: TokenBundle) -> None:
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(asdict(bundle), fh, indent=2)
        os.replace(tmp, self.path)  # atomic on POSIX

    def clear(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
