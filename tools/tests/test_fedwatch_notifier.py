import unittest

from tools import fedwatch_notifier


class ExtractProbabilityTests(unittest.TestCase):
    def test_extracts_from_nested_dict(self):
        payload = {"outer": [{"Ease": "32.5%"}, {"other": 1}]}
        self.assertEqual(fedwatch_notifier.find_ease_probability(payload), 32.5)

    def test_returns_none_when_missing(self):
        payload = {"outer": [{"unchanged": "60%"}]}
        self.assertIsNone(fedwatch_notifier.find_ease_probability(payload))

    def test_handles_numeric_without_percent(self):
        payload = {"details": {"easeProbability": 12}}
        self.assertEqual(fedwatch_notifier.find_ease_probability(payload), 12.0)


class MessagingTests(unittest.TestCase):
    def test_builds_initial_message(self):
        message = fedwatch_notifier.build_change_message("http://example", None, 15.5)
        self.assertIn("15.5%", message)
        self.assertIn("monitoring started", message)

    def test_builds_change_message(self):
        message = fedwatch_notifier.build_change_message("http://example", 10, 12.5)
        self.assertIn("from 10% to 12.5%", message)


if __name__ == "__main__":
    unittest.main()
