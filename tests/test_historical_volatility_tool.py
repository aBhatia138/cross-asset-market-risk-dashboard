import unittest
from unittest.mock import patch

import pandas as pd

from src.tool_registry import execute_tool

class TestHistoricalVolatilityValdiation(unittest.TestCase):

    def setUp(self):
        self.arguments = {
            "ric": "XAU=",
            "start_date": "2025-11-09",
            "end_date": "2026-11-09",
            "window": 21
        }

    def test_missing_arguments(self):
        result = execute_tool(
            "get_historical_volatility",
            {}
        )

        self.assertFalse(result["success"])

    def test_unexpected_argument(self):
        arguments = self.arguments.copy()
        arguments["invalid_argument"] = 123

        result = execute_tool(
            "get_historical_volatility",
            arguments
        )

        self.assertFalse(result["success"])

    def test_unsupported_asset(self):
        arguments = self.arguments.copy()
        arguments["ric"] = "INVALID"

        result = execute_tool(
            "get_historical_volatility",
            arguments
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "Unsupported instrument RIC"
        )

    def test_invalid_window(self):
        invalid_windows = [1, 0, -5, 2.5, True, "21"]

        for window in invalid_windows:
            with self.subTest(window=window):
                arguments = self.arguments.copy()
                arguments["window"] = window

                result = execute_tool(
                    "get_historical_volatility",
                    arguments
                )

                self.assertFalse(result["success"])

        def test_invalid_date_range(self):
            arguments = self.arguments.copy()
            arguments["start_date"] = "invalid-date"

            result = execute_tool(
                "get_historical_volatility",
                arguments
            )

            self.assertFalse(result["success"])


class TestHistoricalVolatilityExecution(unittest.TestCase):

    def setUp(self):

        self.arguments = {
            "ric": "XAU=",
            "start_date": "2025-11-09",
            "end_date": "2026-11-09",
            "window": 5
        }

        self.dates = pd.date_range(
            "2026-01-01",
            periods=4,
            freq="D"
        )

        self.prices = pd.Series(
            [100, 101, 102, 103],
            index=self.dates,
            name="XAU="
        )

        self.returns = pd.DataFrame(
            {
                "XAU=": [0.01, 0.02, -0.01]
            },
            index=self.dates[1:]
        )

        self.rolling_volatility = pd.DataFrame(
            {
                "XAU=": [0.20, 0.22, 0.24]
            },
            index=self.dates[1:]
        )

    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_live_feed")
    @patch("src.tool_registry.open_lseg_session")

    def test_valid_execution(
        self,
        mock_session,
        mock_fetch,
        mock_returns,
        mock_rolling
    ):

        mock_fetch.return_value = self.prices
        mock_returns.return_value = self.returns
        mock_rolling.return_value = self.rolling_volatility

        result = execute_tool(
            "get_historical_volatility",
            self.arguments
        )

        self.assertTrue(result["success"])

        self.assertEqual(
            result["tool"],
            "get_historical_volatility"
        )

        self.assertEqual(result["ric"], "XAU=")
        self.assertEqual(result["asset"], "Gold")
        self.assertEqual(result["window"], 5)
        self.assertEqual(result["observations"], 3)

        self.assertAlmostEqual(
            result["latest_annualized_volatility"],
            0.24
        )

        self.assertIn("date_range", result)

        mock_session.assert_called_once()
        mock_fetch.assert_called_once()
        mock_returns.assert_called_once()
        mock_rolling.assert_called_once()

    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_live_feed")
    @patch("src.tool_registry.open_lseg_session")

    def test_default_window(
        self,
        mock_session,
        mock_fetch,
        mock_returns,
        mock_rolling
    ):

        mock_fetch.return_value = self.prices
        mock_returns.return_value = self.returns
        mock_rolling.return_value = self.rolling_volatility

        arguments = self.arguments.copy()
        arguments.pop("window")

        result = execute_tool(
            "get_historical_volatility",
            arguments
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["window"], 21)

        mock_rolling.assert_called_once()

        self.assertEqual(
            mock_rolling.call_args.kwargs["window"],
            21
        )

    @patch("src.tool_registry.fetch_live_feed")
    @patch("src.tool_registry.open_lseg_session")
    def test_empty_historical_prices(
        self,
        mock_session,
        mock_fetch
    ):

        mock_fetch.return_value = pd.Series(dtype=float)

        result = execute_tool(
            "get_historical_volatility",
            self.arguments
        )

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_live_feed")
    @patch("src.tool_registry.open_lseg_session")

    def test_insufficient_observations(
        self,
        mock_session,
        mock_fetch,
        mock_returns,
        mock_rolling
    ):

        mock_fetch.return_value = self.prices
        mock_returns.return_value = self.returns

        mock_rolling.return_value = pd.DataFrame(
            {"XAU=": [float("nan")] * 3},
            index=self.dates[1:]
        )

        result = execute_tool(
            "get_historical_volatility",
            self.arguments
        )

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("src.tool_registry.fetch_live_feed")
    @patch("src.tool_registry.open_lseg_session")
    def test_historical_data_retrieval_failure(
        self,
        mock_session,
        mock_fetch
    ):

        mock_fetch.side_effect = ValueError(
            "Historical data unavailable"
        )

        result = execute_tool(
            "get_historical_volatility",
            self.arguments
        )

        self.assertFalse(result["success"])
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()