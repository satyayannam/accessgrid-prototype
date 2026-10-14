"""Public API-shaped simulation. This module never sends network requests."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from models import AccessPass, utcnow

BASE = "https://api.accessgrid.com/v1/key-cards"
HEADERS = {"X-ACCT-ID": "<ACCOUNT_ID>", "X-PAYLOAD-SIG": "<HMAC_SIGNATURE>",
           "Content-Type": "application/json"}
TRANSITIONS = {
    "activate": ({"created"}, "active", "activated"),
    "suspend": ({"active"}, "suspended", "suspended"),
    "resume": ({"suspended"}, "active", "resumed"),
    "unlink": ({"active", "suspended"}, "unlink", "unlinked"),
    "delete": ({"created", "active", "suspended", "unlink"}, "deleted", "deleted"),
}


def make_payload(full_name="Demo Employee 001", email="demo001@example.invalid",
                 employee_id="DEMO-001", department="Engineering", title="Demo Engineer",
                 site="Demo Lab A", classification="full_time", template="tpl_demo_apple"):
    now = datetime.now(timezone.utc)
    return {"card_template_id": template, "full_name": full_name.strip(), "email": email.strip(),
            "employee_id": employee_id.strip(), "department": department, "title": title,
            "site_name": site, "classification": classification,
            "site_code": "42", "card_number": "1001",
            "start_date": now.isoformat(), "expiration_date": (now + timedelta(days=90)).isoformat(),
            "metadata": {"synthetic": True, "department": department, "site": site}}


class MockAccessGrid:
    def __init__(self):
        self.passes: dict[str, AccessPass] = {}
        self.events: list[dict] = []
        self.last_exchange: dict = {}
        self._last_generated_time: datetime | None = None

    def _event(self, card: AccessPass, verb: str) -> dict:
        # Windows clock resolution can repeat. Give sequential demo actions
        # distinct logical timestamps without weakening the receiver's guard.
        stamp = datetime.fromisoformat(utcnow().replace("Z", "+00:00"))
        if self._last_generated_time is not None and stamp <= self._last_generated_time:
            stamp = self._last_generated_time + timedelta(microseconds=1)
        self._last_generated_time = stamp
        data = card.snapshot()
        # Device detail is a demo enrichment; the published event example is a subset.
        data["card_templates"] = [{"id": card.payload["card_template_id"],
                                   "platform": card.platform, "protocol": "desfire",
                                   "name": "Synthetic employee badge"}]
        event = {"specversion": "1.0", "id": "evt_demo_" + uuid4().hex[:12],
                 "source": "/accessgrid/customer", "type": "ag.access_pass." + verb,
                 "dataschema": "https://api.accessgrid.com/schemas/access_pass/v1.0.3.json",
                 "time": stamp.isoformat(timespec="microseconds").replace("+00:00", "Z"), "data": data}
        self.events.append(deepcopy(event))
        return deepcopy(event)

    def issue(self, payload: dict, platform="apple") -> tuple[AccessPass, dict]:
        for key in ("full_name", "employee_id", "card_template_id"):
            if not str(payload.get(key, "")).strip():
                raise ValueError(f"{key} is required.")
        if not payload.get("email", "").endswith("@example.invalid"):
            raise ValueError("Use an obvious synthetic email ending in @example.invalid.")
        if platform not in {"apple", "android"}:
            raise ValueError("Choose apple or android.")
        if not payload["card_template_id"].startswith("tpl_demo_"):
            raise ValueError("Use a synthetic template ID starting with tpl_demo_.")
        card = AccessPass("key_demo_" + uuid4().hex[:10], deepcopy(payload), platform)
        self.passes[card.id] = card
        self.last_exchange = {"request": {"method": "POST", "endpoint": BASE,
                              "headers": HEADERS.copy(), "json": deepcopy(payload)},
                              "mock_response": {"status": "success", **card.snapshot()}}
        return card, self._event(card, "issued")

    def transition(self, card_id: str, action: str) -> dict:
        card = self.passes[card_id]
        if action not in TRANSITIONS:
            raise ValueError("Unsupported action.")
        allowed, target, verb = TRANSITIONS[action]
        request = ({"kind": "SIMULATED WALLET INSTALL", "note": "Device-side action; no public activation API claimed."}
                   if action == "activate" else {"method": "POST", "endpoint": f"{BASE}/{card_id}/{action}",
                   "headers": HEADERS.copy(), "json": {"card_id": card_id}})
        if card.state not in allowed:
            message = f"Cannot {action} a pass in '{card.state}'. Expected: {', '.join(sorted(allowed))}."
            self.last_exchange = {"request": request, "mock_response": {"local_validation_error": message}}
            raise ValueError(message)
        card.state = target
        if action == "activate":
            card.devices = [{"id": "device_demo_001", "platform": card.platform,
                             "model": "Synthetic test device", "state": "active"}]
        for device in card.devices:
            device["state"] = target
        self.last_exchange = {"request": request, "mock_response": {"status": "success", **card.snapshot()}}
        return self._event(card, verb)

    def delayed_event(self, card_id: str) -> dict:
        """Distinct, older event tests ordering rather than the duplicate guard."""
        event = deepcopy(next(e for e in self.events if e["data"]["id"] == card_id))
        event["id"] = "evt_demo_delayed_" + uuid4().hex[:8]
        stamp = datetime.fromisoformat(event["time"].replace("Z", "+00:00"))
        event["time"] = (stamp - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")
        self.events.append(deepcopy(event))
        return event
