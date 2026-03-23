import unittest
from datetime import datetime, timezone

from app.services.datetime_utils import ensure_utc_datetime


class DateTimeUtilsTests(unittest.TestCase):
    def test_naive_datetime_is_assumed_to_be_utc(self) -> None:
        naive_value = datetime(2026, 3, 23, 0, 41, 28)

        normalized_value = ensure_utc_datetime(naive_value)

        self.assertIsNotNone(normalized_value)
        self.assertEqual(normalized_value.tzinfo, timezone.utc)
        self.assertEqual(normalized_value.isoformat(), "2026-03-23T00:41:28+00:00")


if __name__ == "__main__":
    unittest.main()
