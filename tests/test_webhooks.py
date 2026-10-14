from copy import deepcopy
import unittest
from mock_accessgrid import MockAccessGrid, make_payload
from event_processor import EventProcessor


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.api = MockAccessGrid()
        self.processor = EventProcessor()
        self.card, self.event = self.api.issue(make_payload())

    def test_duplicate_idempotency(self):
        self.processor.deliver(self.event)
        result = self.processor.deliver(self.event)
        self.assertEqual((result.http_status, result.outcome), (200, "duplicate"))
        self.assertEqual(self.processor.business_actions, 1)

    def test_failure_remains_retryable(self):
        result = self.processor.deliver(self.event, fail=True)
        self.assertEqual(result.http_status, 500)
        self.assertFalse(self.processor.processed_ids)
        self.assertFalse(self.processor.local)
        self.assertEqual(self.processor.deliver(self.event).outcome, "processed")

    def test_out_of_order_preserves_newer_state(self):
        active = self.api.transition(self.card.id, "activate")
        self.processor.deliver(active)
        result = self.processor.deliver(self.event)
        self.assertEqual(result.outcome, "out_of_order")
        self.assertEqual(self.processor.local[self.card.id]["state"], "active")
        self.assertEqual(self.processor.business_actions, 1)

    def test_delayed_fixture_is_not_a_duplicate(self):
        self.processor.deliver(self.event)
        delayed = self.api.delayed_event(self.card.id)
        self.assertNotEqual(delayed["id"], self.event["id"])
        self.assertEqual(self.processor.deliver(delayed).outcome, "out_of_order")

    def test_equal_timestamp_is_ambiguous(self):
        self.processor.deliver(self.event)
        conflict = deepcopy(self.event)
        conflict["id"] = "evt_demo_other"
        conflict["data"]["state"] = "deleted"
        self.assertEqual(self.processor.deliver(conflict).outcome, "out_of_order")
        self.assertEqual(self.processor.local[self.card.id]["state"], "created")

    def test_failure_then_recovery_closes_mismatch(self):
        self.processor.deliver(self.event)
        active = self.api.transition(self.card.id, "activate")
        self.processor.deliver(active, fail=True)
        self.assertNotEqual(self.card.state, self.processor.local[self.card.id]["state"])
        self.processor.deliver(active)
        self.assertEqual(self.card.state, self.processor.local[self.card.id]["state"])


if __name__ == "__main__":
    unittest.main()
