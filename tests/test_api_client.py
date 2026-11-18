import unittest

from ingest.api_client import redact


class TestRedact(unittest.TestCase):
    def test_key_removed_from_error_text(self):
        text = "Max retries exceeded with url: /resource/x?api-key=579bSECRET&format=json (Caused by ...)"
        self.assertEqual(redact(text),
                         "Max retries exceeded with url: /resource/x?api-key=***&format=json (Caused by ...)")


if __name__ == "__main__":
    unittest.main()
