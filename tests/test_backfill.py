import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from ingest.api_client import ApiUnavailableError
from ingest.backfill import ingest_dates


class FakeClient:
    def __init__(self, fail_for=()):
        self.fail_for = fail_for

    def fetch_all(self, filters):
        if filters["Commodity"] in self.fail_for:
            raise ApiUnavailableError("down")
        return [{"Market": "B"}, {"Market": "A"}]


@mock.patch("ingest.backfill.PAUSE_SECONDS", 0)
class TestIngestDates(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.folder = Path(self.out, "arrival_date=2026-11-20")

    def test_writes_files_and_manifest(self):
        failed = ingest_dates(FakeClient(), [date(2026, 11, 20)], ["Onion", "Potato"], self.out)
        self.assertEqual(failed, [])
        manifest = json.loads((self.folder / "_manifest.json").read_text())
        self.assertEqual(manifest["rows"], {"Onion": 2, "Potato": 2})
        records = json.loads((self.folder / "commodity=Onion.json").read_text())
        self.assertEqual([r["Market"] for r in records], ["A", "B"])  # sorted for identical reruns

    def test_failure_is_reported_and_manifest_skipped(self):
        failed = ingest_dates(FakeClient(fail_for={"Potato"}), [date(2026, 11, 20)],
                              ["Onion", "Potato"], self.out)
        self.assertEqual(failed, [(date(2026, 11, 20), "Potato")])
        self.assertTrue((self.folder / "commodity=Onion.json").exists())
        self.assertFalse((self.folder / "_manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
