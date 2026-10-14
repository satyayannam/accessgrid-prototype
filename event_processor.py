"""In-memory inbox and projection. Production needs an atomic durable transaction."""
from copy import deepcopy
from datetime import datetime
from models import Delivery, utcnow


class EventProcessor:
    def __init__(self):
        self.processed_ids: set[tuple[str, str]] = set()
        self.local: dict[str, dict] = {}
        self.watermarks: dict[str, datetime] = {}
        self.deliveries: list[Delivery] = []
        self.business_actions = 0

    def deliver(self, event: dict, fail=False) -> Delivery:
        card_id = event["data"]["id"]
        key = (event["source"], event["id"])
        stamp = datetime.fromisoformat(event["time"].replace("Z", "+00:00"))
        if fail:
            status, outcome, message = 500, "failed", "Consumer failure. Event remains retryable; no state committed."
        elif key in self.processed_ids:
            status, outcome, message = 200, "duplicate", "Duplicate event detected — safely ignored."
        elif card_id in self.watermarks and stamp <= self.watermarks[card_id]:
            status, outcome, message = 200, "out_of_order", "Older or equal timestamp: state preserved. Reconcile with authoritative GET in production."
            self.processed_ids.add(key)
        else:
            status, outcome, message = 200, "processed", "Local projection updated once."
            self.local[card_id] = deepcopy(event["data"])
            self.watermarks[card_id] = stamp
            self.processed_ids.add(key)
            self.business_actions += 1
        delivery = Delivery(event["id"], card_id, utcnow(), status, outcome,
                            8 + len(self.deliveries) % 7, message)
        self.deliveries.append(delivery)
        return delivery
