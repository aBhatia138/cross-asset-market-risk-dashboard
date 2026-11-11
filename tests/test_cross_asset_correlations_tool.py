
import unittest
from unittest.mock import patch

import pandas as pd

from src.tool_registry import execute_tool, dataframe_to_dict


class TestCrossAssetCorrelationsValidation(unittest.TestCase):

    def setUp(self):
        self.arguments = {
            "selected_assets": "XAU=,EUR=,JPY=",
            "start_date": "2025-11-09",
            "end_date": "2026-11-09",
            "min_observations": 30
        }

    def test_missing_arguments(self):
        result = execute_tool(
            "get_cross_asset_correlations",
            {}
        )

        self.assertFalse(result["success"])

    def test_unexpected_argument(self):
        arguments = self.arguments.copy()
        arguments["invalid_argument"] = 123

        result = execute_tool(
            "get_cross_asset_correlations",
            arguments
        )

        self.assertFalse(result["success"])

    def test_unsupported_asset(self):
        arguments = self.arguments.copy()
        arguments["selected_assets"] = "XAU=,INVALID"

        result = execute_tool(
            "get_cross_asset_correlations",
            arguments
        )

        self.assertFalse(result["success"])

    def test_invalid_date_range(self):
        arguments = self.arguments.copy()
        arguments["start_date"] = "invalid-date"

        result = execute_tool(
            "get_cross_asset_correlations",
            arguments
        )

        self.assertFalse(result["success"])

    def test_invalid_min_observations(self):

        invalid_values = [1, 0, -5, 2.5, True, "30"]

        for value in invalid_values:
            with self.subTest(value=value):
                arguments = self.arguments.copy()
                arguments["min_observations"] = value

                result = execute_tool(
                    "get_cross_asset_correlations",
                    arguments
                )

                self.assertFalse(result["success"])


class TestCrossAssetCorrelationsExecution(unittest.TestCase):

    def setUp(self):

        self.arguments = {
            "selected_assets": "XAU=,EUR=,JPY=",
            "start_date": "2025-11-09",
            "end_date": "2026-11-09",
            "min_observations": 2
        }

        self.dates = pd.date_range(
            "2026-01-01",
            periods=4,
            freq="D"
        )

        self.prices = pd.DataFrame(
            {
                "XAU=": [100, 101, 102, 103],
                "EUR=": [1.10, 1.11, 1.12, 1.13],
                "JPY=": [150, 151, 152, 153]
            },
            index=self.dates
        )

        self.returns = pd.DataFrame(
            {
                "XAU=": [0.01, 0.02, 0.01],
                "EUR=": [0.02, 0.01, 0.03],
                "JPY=": [-0.01, 0.01, 0.02]
            },
            index=self.dates[1:]
        )

        self.correlation_matrix = pd.DataFrame(
            [
                [1.0, 0.8, 0.5],
                [0.8, 1.0, 0.3],
                [0.5, 0.3, 1.0]
            ],
            index=["XAU=", "EUR=", "JPY="],
            columns=["XAU=", "EUR=", "JPY="]
        )

        self.observation_counts = pd.DataFrame(
            [
                [3, 3, 3],
                [3, 3, 3],
                [3, 3, 3]
            ],
            index=["XAU=", "EUR=", "JPY="],
            columns=["XAU=", "EUR=", "JPY="]
        )

    @patch("src.tool_registry.calculate_corr_matrix")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    @patch("src.tool_registry.open_lseg_session")
    def test_valid_execution(
        self,
        mock_session,
        mock_fetch,
        mock_returns,
        mock_correlations
    ):

        mock_fetch.return_value = (
            self.prices,
            {}
        )

        mock_returns.return_value = self.returns

        mock_correlations.return_value = (
            self.correlation_matrix,
            self.observation_counts
        )

        result = execute_tool(
            "get_cross_asset_correlations",
            self.arguments
        )

        self.assertTrue(result["success"])

        self.assertEqual(
            result["tool"],
            "get_cross_asset_correlations"
        )

        self.assertEqual(
            result["min_observations"],
            2
        )

        self.assertEqual(
            [asset["ric"] for asset in result["assets"]],
            ["XAU=", "EUR=", "JPY="]
        )

        self.assertEqual(
            [asset["name"] for asset in result["assets"]],
            ["Gold", "EUR/USD", "JPY/USD"]
        )

        self.assertEqual(
            result["correlation_matrix"],
            dataframe_to_dict(self.correlation_matrix)
        )

        self.assertEqual(
            result["observation_counts"],
            dataframe_to_dict(self.observation_counts)
        )

        self.assertEqual(result["failures"], {})

        mock_session.assert_called_once()
        mock_fetch.assert_called_once()
        mock_returns.assert_called_once()
        mock_correlations.assert_called_once()

    @patch("src.tool_registry.calculate_corr_matrix")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    @patch("src.tool_registry.open_lseg_session")
    def test_default_min_observations(
        self,
        mock_session,
        mock_fetch,
        mock_returns,
        mock_correlations
    ):

        mock_fetch.return_value = (
            self.prices,
            {}
        )

        mock_returns.return_value = self.returns

        mock_correlations.return_value = (
            self.correlation_matrix,
            self.observation_counts
        )

        arguments = self.arguments.copy()
        arguments.pop("min_observations")

        result = execute_tool(
            "get_cross_asset_correlations",
            arguments
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["min_observations"], 30)

        mock_correlations.assert_called_once()

        self.assertEqual(
            mock_correlations.call_args.kwargs["min_observations"],
            30
        )

    @patch("src.tool_registry.fetch_multiple_assets")
    @patch("src.tool_registry.open_lseg_session")
    def test_insufficient_assets_retrieved(
        self,
        mock_session,
        mock_fetch
    ):

        partial_prices = self.prices[["XAU="]]

        mock_fetch.return_value = (
            partial_prices,
            {
                "EUR=": "Historical data unavailable",
                "JPY=": "Historical data unavailable"
            }
        )

        result = execute_tool(
            "get_cross_asset_correlations",
            self.arguments
        )

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("src.tool_registry.calculate_corr_matrix")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    @patch("src.tool_registry.open_lseg_session")
    def test_partial_data_retrieval(
        self,
        mock_session,
        mock_fetch,
        mock_returns,
        mock_correlations
    ):

        partial_prices = self.prices[["XAU=", "EUR="]]

        failures = {
            "JPY=": "Historical data unavailable"
        }

        mock_fetch.return_value = (
            partial_prices,
            failures
        )

        mock_returns.return_value = self.returns[
            ["XAU=", "EUR="]
        ]

        partial_correlations = self.correlation_matrix[
            ["XAU=", "EUR="]
        ].loc[["XAU=", "EUR="]]

        partial_counts = self.observation_counts[
            ["XAU=", "EUR="]
        ].loc[["XAU=", "EUR="]]

        mock_correlations.return_value = (
            partial_correlations,
            partial_counts
        )

        result = execute_tool(
            "get_cross_asset_correlations",
            self.arguments
        )

        self.assertTrue(result["success"])

        self.assertEqual(
            [asset["ric"] for asset in result["assets"]],
            ["XAU=", "EUR="]
        )

        self.assertEqual(
            result["failures"],
            failures
        )

        self.assertNotIn(
            "JPY=",
            [asset["ric"] for asset in result["assets"]]
        )

    @patch("src.tool_registry.fetch_multiple_assets")
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
            "get_cross_asset_correlations",
            self.arguments
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "Unable to calculate cross-asset correlations."
        )


if __name__ == "__main__":
    unittest.main()
