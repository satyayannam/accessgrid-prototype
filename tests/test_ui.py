import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()

    def click(self, label):
        next(b for b in self.app.button if b.label == label).click().run()
        self.assertFalse(self.app.exception)

    def test_meeting_flow_and_all_controls(self):
        self.assertFalse(self.app.exception)
        self.click("Issue Pass")
        self.click("Simulate wallet install")
        self.click("Suspend")
        self.click("Duplicate delivery")
        self.assertEqual(self.app.session_state.processor.business_actions, 3)
        self.click("Consumer failure · 500")
        self.click("Deliver / retry · 200")
        self.click("Delayed / out-of-order")
        self.click("Resume")
        self.click("Resume")
        self.assertIn("Cannot resume", self.app.session_state.notice)
        self.click("Unlink")
        self.click("Delete")
        scenarios = next(s for s in self.app.selectbox if s.label == "What are you investigating?")
        for option in scenarios.options:
            scenarios.select(option).run()
            self.assertFalse(self.app.exception)
        self.click("Reset demo")
        self.assertFalse(self.app.session_state.api.passes)

    def test_multiple_passes_and_failed_lifecycle(self):
        self.click("Issue Pass")
        self.click("Issue Pass")
        self.assertEqual(len(self.app.session_state.api.passes), 2)
        self.app.checkbox(key="fail_next").check().run()
        self.click("Simulate wallet install")
        selected = self.app.session_state.selected_pass
        self.assertEqual(self.app.session_state.processor.local[selected]["state"], "created")
        self.click("Deliver / retry · 200")
        self.assertEqual(self.app.session_state.processor.local[selected]["state"], "active")


if __name__ == "__main__":
    unittest.main()
