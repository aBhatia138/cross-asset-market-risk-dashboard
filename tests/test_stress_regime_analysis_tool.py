
import unittest
from unittest.mock import patch

import pandas as pd

from src.tool_registry import execute_tool

import json 

class TestStressRegimeAnalysisValidation(unittest.TestCase):

    def setUp(self):
        self.arguments = {
            "selected_assets": "XAU=,EUR=,JPY=,.STOXX50E",
            "stress_ric": ".STOXX50E",
            "start_date": "2025-11-08",
            "end_date": "2026-11-08",
            "window": 21,
            "percentile": 0.80,
            "min_observations": 30
        }

    def test_missing_arguments(self):
        result = execute_tool(
            "get_stress_regime_analysis",
            {}
        )

        self.assertFalse(result["success"])

    def test_unsupported_asset(self):
        arguments = self.arguments.copy()
        arguments["selected_assets"] = "XAU=,INVALID"

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])

    def test_unsupported_stress_indicator(self):
        arguments = self.arguments.copy()
        arguments["stress_ric"] = "INVALID"

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "Unsupported stress indicator RIC."
        )

    def test_stress_indicator_not_selected(self):
        arguments = self.arguments.copy()
        arguments["stress_ric"] = "EUR="

        arguments["selected_assets"] = "XAU=,JPY="

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "The stress indicator must also be included "
            "in selected_assets."
        )

    def test_invalid_window(self):
        arguments = self.arguments.copy()
        arguments["window"] = 1

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])

    def test_invalid_percentile(self):
        arguments = self.arguments.copy()
        arguments["percentile"] = 1.0

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])

    def test_invalid_min_observations(self):
        arguments = self.arguments.copy()
        arguments["min_observations"] = 1

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])


class TestStressRegimeAnalysisExecution(unittest.TestCase):

    def setUp(self):
        self.arguments = {
            "selected_assets": "XAU=,EUR=,JPY=,.STOXX50E",
            "stress_ric": ".STOXX50E",
            "start_date": "2025-11-08",
            "end_date": "2026-11-08",
            "window": 21,
            "percentile": 0.80,
            "min_observations": 30
        }

        self.dates = pd.date_range(
            "2026-01-01",
            periods=4,
            freq="D"
        )

        self.prices = pd.DataFrame(
            {
                "XAU=": [100, 101, 102, 103],
                "EUR=": [1.1, 1.2, 1.1, 1.3],
                "JPY=": [150, 151, 152, 153],
                ".STOXX50E": [6000, 6050, 5900, 5800]
            },
            index=self.dates
        )

        self.returns = pd.DataFrame(
            {
                "XAU=": [0.01, 0.02, 0.01, 0.01],
                "EUR=": [0.01, -0.01, 0.02, 0.01],
                "JPY=": [0.01, 0.01, 0.01, 0.01],
                ".STOXX50E": [0.02, -0.02, -0.03, 0.01]
            },
            index=self.dates
        )

        self.rolling_volatility = pd.DataFrame(
            {
                ".STOXX50E": [0.10, 0.15, 0.20, 0.25]
            },
            index=self.dates
        )

        self.stress_periods = pd.Series(
            [False, False, True, True],
            index=self.dates
        )

        self.regime_statistics = {
            "XAU=": {
                "stress": {
                    "observations": 2,
                    "average_daily_return": 0.01,
                    "annualized_volatility": 0.02
                },
                "non_stress": {
                    "observations": 2,
                    "average_daily_return": 0.015,
                    "annualized_volatility": 0.01
                }
            }
        }

        correlation_matrix = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=["XAU=", "EUR="],
            columns=["XAU=", "EUR="]
        )

        observation_counts = pd.DataFrame(
            [[2, 2], [2, 2]],
            index=["XAU=", "EUR="],
            columns=["XAU=", "EUR="]
        )

        self.conditional_correlations = {
            "stress": {
                "correlation_matrix": correlation_matrix,
                "observation_counts": observation_counts
            },
            "non_stress": {
                "correlation_matrix": correlation_matrix,
                "observation_counts": observation_counts
            }
        }

    @patch("src.tool_registry.calculate_conditional_correlations")
    @patch("src.tool_registry.calculate_regime_statistics")
    @patch("src.tool_registry.identify_stress_periods")
    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    def test_valid_execution(
        self,
        mock_fetch,
        mock_returns,
        mock_rolling,
        mock_stress,
        mock_statistics,
        mock_correlations
    ):

        mock_fetch.return_value = (self.prices, {})
        mock_returns.return_value = self.returns
        mock_rolling.return_value = self.rolling_volatility

        mock_stress.return_value = (
            self.stress_periods,
            0.18
        )

        mock_statistics.return_value = self.regime_statistics

        mock_correlations.return_value = (
            self.conditional_correlations
        )

        result = execute_tool(
            "get_stress_regime_analysis",
            self.arguments
        )

        self.assertTrue(result["success"])

        self.assertEqual(
            result["stress_indicator"]["ric"],
            ".STOXX50E"
        )

        self.assertEqual(
            result["stress_indicator"][
                "annualized_volatility_threshold"
            ],
            0.18
        )

        self.assertEqual(
            result["regime_observations"]["stress"],
            2
        )

        self.assertEqual(
            result["regime_observations"]["non_stress"],
            2
        )

        self.assertIn(
            "regime_statistics",
            result
        )

        self.assertIn(
            "conditional_correlations",
            result
        )

        self.assertEqual(
            result["failures"],
            {}
        )

        mock_fetch.assert_called_once()
        mock_returns.assert_called_once()
        mock_rolling.assert_called_once()
        mock_stress.assert_called_once()
        mock_statistics.assert_called_once()
        mock_correlations.assert_called_once()

    @patch("src.tool_registry.open_lseg_session")
    @patch("src.tool_registry.calculate_conditional_correlations")
    @patch("src.tool_registry.calculate_regime_statistics")
    @patch("src.tool_registry.identify_stress_periods")
    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    def test_json_serialization(
        self,
        mock_fetch,
        mock_returns,
        mock_rolling,
        mock_stress,
        mock_statistics,
        mock_correlations,
        mock_session
    ):

        mock_fetch.return_value = (self.prices, {})
        mock_returns.return_value = self.returns
        mock_rolling.return_value = self.rolling_volatility

        mock_stress.return_value = (
            self.stress_periods,
            0.18
        )

        mock_statistics.return_value = self.regime_statistics

        mock_correlations.return_value = (
            self.conditional_correlations
        )

        result = execute_tool(
            "get_stress_regime_analysis",
            self.arguments
        )

        self.assertTrue(result["success"])

        # This should not raise a TypeError.
        serialized_result = json.dumps(result)

        # Confirm that the serialized result is valid JSON.
        deserialized_result = json.loads(serialized_result)

        self.assertEqual(
            deserialized_result["success"],
            True
        )

        self.assertIn(
            "conditional_correlations",
            deserialized_result
        )

    @patch("src.tool_registry.open_lseg_session")
    @patch("src.tool_registry.identify_stress_periods")
    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    def test_no_classified_observations(
        self,
        mock_fetch,
        mock_returns,
        mock_rolling,
        mock_stress,
        mock_session
    ):

        mock_fetch.return_value = (self.prices, {})
        mock_returns.return_value = self.returns
        mock_rolling.return_value = self.rolling_volatility

        # Simulate a situation where no dates can be classified.
        empty_stress_periods = pd.Series(
            dtype=bool,
            index=pd.DatetimeIndex([])
        )

        mock_stress.return_value = (
            empty_stress_periods,
            0.18
        )

        result = execute_tool(
            "get_stress_regime_analysis",
            self.arguments
        )

        self.assertFalse(result["success"])

        self.assertEqual(
            result["error"],
            "Unable to complete stress regime analysis."
        )

        mock_fetch.assert_called_once()
        mock_stress.assert_called_once()
        mock_session.assert_called_once()

    @patch("src.tool_registry.open_lseg_session")
    @patch("src.tool_registry.calculate_conditional_correlations")
    @patch("src.tool_registry.calculate_regime_statistics")
    @patch("src.tool_registry.identify_stress_periods")
    @patch("src.tool_registry.calculate_rolling_volatility")
    @patch("src.tool_registry.calculate_daily_returns")
    @patch("src.tool_registry.fetch_multiple_assets")
    def test_partial_asset_retrieval(
        self,
        mock_fetch,
        mock_returns,
        mock_rolling,
        mock_stress,
        mock_statistics,
        mock_correlations,
        mock_session
    ):

        # Only three of the four requested assets are retrieved.
        partial_prices = self.prices[
            ["XAU=", "EUR=", ".STOXX50E"]
        ]

        failures = {
            "JPY=": "Historical data unavailable"
        }

        mock_fetch.return_value = (
            partial_prices,
            failures
        )

        mock_returns.return_value = self.returns[
            ["XAU=", "EUR=", ".STOXX50E"]
        ]

        mock_rolling.return_value = self.rolling_volatility

        mock_stress.return_value = (
            self.stress_periods,
            0.18
        )

        mock_statistics.return_value = self.regime_statistics

        mock_correlations.return_value = (
            self.conditional_correlations
        )

        result = execute_tool(
            "get_stress_regime_analysis",
            self.arguments
        )

        self.assertTrue(result["success"])

        retrieved_rics = [
            asset["ric"]
            for asset in result["assets"]
        ]

        self.assertNotIn("JPY=", retrieved_rics)
        self.assertIn(".STOXX50E", retrieved_rics)

        self.assertEqual(
            result["failures"],
            failures
        )

        mock_session.assert_called_once()
        mock_fetch.assert_called_once()

    @patch("src.tool_registry.fetch_multiple_assets")
    def test_stress_indicator_retrieval_failure(self, mock_fetch):

        # Only two assets are returned, but neither is the stress indicator.
        partial_prices = self.prices[["XAU=", "EUR="]]

        mock_fetch.return_value = (
            partial_prices,
            {".STOXX50E": "Historical data unavailable"}
        )

        result = execute_tool(
            "get_stress_regime_analysis",
            self.arguments
        )

        self.assertFalse(result["success"])

    def test_unexpected_argument(self):
        arguments = self.arguments.copy()
        arguments["unexpected"] = "value"

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(result["success"])

    def test_invalid_date_range(self):
        arguments = self.arguments.copy()
        arguments["start_date"] = "2026-11-08"
        arguments["end_date"] = "2025-11-08"

        result = execute_tool(
            "get_stress_regime_analysis",
            arguments
        )

        self.assertFalse(
            result["success"]
        )


if __name__ == "__main__":
    unittest.main()
