import unittest
from unittest.mock import patch
from mock_accessgrid import MockAccessGrid, make_payload


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.api = MockAccessGrid()
        self.card, self.issued = self.api.issue(make_payload())

    def test_issue_contract(self):
        self.assertEqual(self.card.state, "created")
        self.assertEqual(self.issued["type"], "ag.access_pass.issued")
        self.assertTrue(self.card.snapshot()["install_url"].startswith("https://wallet.example.invalid/"))
        self.assertEqual(self.api.last_exchange["request"]["headers"]["X-PAYLOAD-SIG"], "<HMAC_SIGNATURE>")

    def test_suspend_resume(self):
        self.api.transition(self.card.id, "activate")
        self.api.transition(self.card.id, "suspend")
        self.assertEqual(self.card.state, "suspended")
        event = self.api.transition(self.card.id, "resume")
        self.assertEqual(self.card.state, "active")
        self.assertEqual(event["type"], "ag.access_pass.resumed")
        self.assertEqual(self.issued["data"]["state"], "created")

    def test_invalid_transition_does_not_emit(self):
        for action in ("suspend", "resume", "unlink"):
            with self.assertRaises(ValueError):
                self.api.transition(self.card.id, action)
        self.assertEqual(len(self.api.events), 1)
        self.api.transition(self.card.id, "activate")
        with self.assertRaisesRegex(ValueError, "Cannot resume"):
            self.api.transition(self.card.id, "resume")

    def test_unlink_and_terminal_delete(self):
        self.api.transition(self.card.id, "activate")
        self.api.transition(self.card.id, "unlink")
        self.assertEqual(self.card.state, "unlink")
        with self.assertRaises(ValueError):
            self.api.transition(self.card.id, "resume")
        self.api.transition(self.card.id, "delete")
        self.assertEqual(self.api.last_exchange["request"]["method"], "POST")
        self.assertTrue(self.api.last_exchange["request"]["endpoint"].endswith("/delete"))
        for action in ("activate", "suspend", "resume", "unlink", "delete"):
            with self.assertRaises(ValueError):
                self.api.transition(self.card.id, action)

    def test_input_validation(self):
        for patch in ({"full_name": ""}, {"email": "demo@example.com"}, {"card_template_id": "real"}):
            with self.assertRaises(ValueError):
                self.api.issue({**make_payload(), **patch})

    def test_google_platform(self):
        card, event = self.api.issue(make_payload(template="tpl_demo_android"), "android")
        self.assertEqual(event["data"]["card_templates"][0]["platform"], "android")

    def test_repeated_clock_does_not_make_sequential_actions_ambiguous(self):
        with patch("mock_accessgrid.utcnow", return_value="2026-10-13T12:00:00.000000Z"):
            api = MockAccessGrid()
            card, issued = api.issue(make_payload())
            active = api.transition(card.id, "activate")
            self.assertGreater(active["time"], issued["time"])


if __name__ == "__main__":
    unittest.main()
