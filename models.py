"""Synthetic domain objects; no credentials or HTTP clients."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from copy import deepcopy


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass
class AccessPass:
    id: str
    payload: dict[str, Any]
    platform: str
    state: str = "created"
    devices: list[dict] = field(default_factory=list)

    def snapshot(self) -> dict:
        return deepcopy({**self.payload, "id": self.id, "state": self.state,
                         "install_url": f"https://wallet.example.invalid/install/{self.id}",
                         "temporary": False, "devices": self.devices})


@dataclass
class Delivery:
    event_id: str
    pass_id: str
    received_at: str
    http_status: int
    outcome: str
    latency_ms: int
    message: str
