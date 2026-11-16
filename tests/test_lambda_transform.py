import unittest
from datetime import date

from transform.lambda_transform import dates_from_event


class TestDatesFromEvent(unittest.TestCase):
    def test_s3_event(self):
        event = {"Records": [{"s3": {"bucket": {"name": "b"},
                                     "object": {"key": "raw/arrival_date%3D2026-11-20/_manifest.json"}}}]}
        self.assertEqual(dates_from_event(event), [("b", date(2026, 11, 20))])


if __name__ == "__main__":
    unittest.main()
