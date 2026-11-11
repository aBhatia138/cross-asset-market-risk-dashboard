import unittest 
from unittest.mock import patch

import pandas as pd

from src.historical_data import fetch_multiple_assets

class TestFetchMultipleAssets(unittest.TestCase):
    def setUp(self):
        
        self.gold_prices = pd.Series(
            [3850.0, 3865.0, 3840.0],
            index=pd.to_datetime([
                "2026-10-01",
                "2026-10-02",
                "2026-10-05"
            ]),
            name="XAU="
        )

        self.eur_prices = pd.Series(
            [1.17, 1.16, 1.18],
            index=pd.to_datetime([
                "2026-10-01",
                "2026-10-05",
                "2026-10-06"
            ]),
            name="EUR="
        )

    @patch("src.historical_data.fetch_live_feed")
    def test_successful_multiple_asset_retrieval(self, mock_fetch):
        """
        Both assets should be retrieved and combined into one DataFrame.
        """

        mock_fetch.side_effect = [
            self.gold_prices,
            self.eur_prices
        ]

        prices, failures = fetch_multiple_assets(
            ["XAU=", "EUR="],
            "2026-10-01",
            "2026-10-06"
        )

        self.assertIsInstance(prices, pd.DataFrame)

        self.assertEqual(
            list(prices.columns),
            ["XAU=", "EUR="]
        )

        self.assertEqual(len(prices), 4)
        self.assertTrue(failures == {})

        mock_fetch.assert_any_call(
            "XAU=", "2026-10-01", "2026-10-06"
        )

        mock_fetch.assert_any_call(
            "EUR=", "2026-10-01", "2026-10-06"
        )

    @patch("src.historical_data.fetch_live_feed")
    def test_outer_join_preserves_all_dates(self, mock_fetch):
        """
        Dates available for only one asset should be retained.
        Missing prices should remain NaN.
        """

        mock_fetch.side_effect = [
            self.gold_prices,
            self.eur_prices
        ]

        prices, failures = fetch_multiple_assets(
            ["XAU=", "EUR="],
            "2026-10-01",
            "2026-10-06"
        )

        self.assertEqual(
            len(prices),
            4
        )

        # October 2 has Gold data but no EUR/USD data
        self.assertTrue(
            pd.isna(prices.loc["2026-10-02", "EUR="])
        )

        # October 6 has EUR/USD data but no Gold data
        self.assertTrue(
            pd.isna(prices.loc["2026-10-06", "XAU="])
        )

        self.assertEqual(failures, {})

    @patch("src.historical_data.fetch_live_feed")
    def test_partial_retrieval_failure(self, mock_fetch):
        """
        Successful assets should be retained if another asset fails.
        """

        mock_fetch.side_effect = [
            self.gold_prices,
            ValueError("LSEG data unavailable")
        ]

        prices, failures = fetch_multiple_assets(
            ["XAU=", "EUR="],
            "2026-10-01",
            "2026-10-06"
        )

        self.assertEqual(
            list(prices.columns),
            ["XAU="]
        )

        self.assertIn("EUR=", failures)

        self.assertEqual(
            failures["EUR="],
            "LSEG data unavailable"
        )

    @patch("src.historical_data.fetch_live_feed")
    def test_all_assets_fail(self, mock_fetch):
        """
        A ValueError should be raised if every retrieval fails.
        """

        mock_fetch.side_effect = ValueError(
            "LSEG connection failed"
        )

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                ["XAU=", "EUR="],
                "2026-10-01",
                "2026-10-06"
            )

    @patch("src.historical_data.fetch_live_feed")
    def test_empty_series_is_recorded_as_failure(self, mock_fetch):
        """
        Empty price Series should be treated as failed retrievals.
        """

        mock_fetch.return_value = pd.Series(
            dtype=float
        )

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                ["XAU="],
                "2026-10-01",
                "2026-10-06"
            )

    @patch("src.historical_data.fetch_live_feed")
    def test_empty_ric_list(self, mock_fetch):

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                [],
                "2026-10-01",
                "2026-10-06"
            )

        mock_fetch.assert_not_called()

    @patch("src.historical_data.fetch_live_feed")
    def test_invalid_ric_list_type(self, mock_fetch):

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                "XAU=",
                "2026-10-01",
                "2026-10-06"
            )

        mock_fetch.assert_not_called()

    @patch("src.historical_data.fetch_live_feed")
    def test_blank_ric(self, mock_fetch):

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                ["XAU=", "   "],
                "2026-10-01",
                "2026-10-06"
            )

        mock_fetch.assert_not_called()

    @patch("src.historical_data.fetch_live_feed")
    def test_duplicate_rics(self, mock_fetch):

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                ["XAU=", "XAU="],
                "2026-10-01",
                "2026-10-06"
            )

        mock_fetch.assert_not_called()

    @patch("src.historical_data.fetch_live_feed")
    def test_invalid_date_range(self, mock_fetch):

        with self.assertRaises(ValueError):
            fetch_multiple_assets(
                ["XAU="],
                "2026-10-06",
                "2026-10-01"
            )

        mock_fetch.assert_not_called()

if __name__ == "__main__":
    unittest.main()