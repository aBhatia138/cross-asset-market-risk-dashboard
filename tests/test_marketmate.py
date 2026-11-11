import unittest
from unittest.mock import patch

from src.marketmate import compare_assets, rank_assets, get_comparison_response

class TestCompareAssets(unittest.TestCase):

    def setUp(self):
        self.selected_assets = {
            "Gold": {"ric": "XAU="},
            "EUR/USD": {"ric": "EUR="}
        }

        self.mock_metrics = {
            "Observations": 250,
            "Annualized Volatility": 0.25,
            "Maximum Drawdown": -0.12,
            "Latest Price": 2500.0,
            "Latest Daily Return": 0.015
        }

    @patch("src.marketmate.get_asset_snapshot")
    def test_compare_assets_preserves_raw_values(self, mock_snapshot):
        mock_snapshot.return_value = {
            "metrics": self.mock_metrics
        }

        for metric_name, expected_value in self.mock_metrics.items():
            with self.subTest(metric=metric_name):
                result = compare_assets(
                    metric_name,
                    self.selected_assets
                )

                self.assertEqual(result["Gold"], expected_value)
                self.assertEqual(result["EUR/USD"], expected_value)

    @patch("src.marketmate.get_asset_snapshot")
    def test_compare_assets_handles_asset_failure(self, mock_snapshot):
        mock_snapshot.side_effect = [
            {"metrics": self.mock_metrics},
            RuntimeError("LSEG data retrieval failed")
        ]

        result = compare_assets(
            "Annualized Volatility",
            self.selected_assets
        )

        self.assertEqual(result["Gold"], 0.25)
        self.assertIsNone(result["EUR/USD"])

    @patch("src.marketmate.get_asset_snapshot")
    def test_compare_assets_handles_missing_metric(self, mock_snapshot):
        mock_snapshot.return_value = {
            "metrics": {
                "Observations": 250
            }
        }

        result = compare_assets(
            "Annualized Volatility",
            self.selected_assets
        )

        self.assertIsNone(result["Gold"])
        self.assertIsNone(result["EUR/USD"])

    def test_compare_assets_rejects_invalid_metric(self):
        with self.assertRaises(ValueError):
            compare_assets(
                "Sharpe Ratio",
                self.selected_assets
            )


class TestRankAssets(unittest.TestCase):

    def test_volatility_ranking_ascending(self):
        comparison = {
            "Gold": 0.25,
            "EUR/USD": 0.08,
            "JPY/USD": 0.12
        }

        result = rank_assets(
            comparison,
            "Annualized Volatility"
        )

        self.assertEqual(
            result,
            [
                ("EUR/USD",0.08),
                ("JPY/USD",0.12),
                ("Gold",0.25)
            ]
        )

    def test_drawdown_ranking_descending(self):

        comparison = {
            "Gold": -0.20,
            "EUR/USD": -0.05,
            "JPY/USD": -0.12
        }

        result = rank_assets(
            comparison,
            "Maximum Drawdown"
        )

        self.assertEqual(
            result,
            [
                ("EUR/USD",-0.05),
                ("JPY/USD",-0.12),
                ("Gold",-0.20)
            ]
        )

    def test_daily_return_ranking_descending(self):

        comparison = {
            "Gold": -0.01,
            "EUR/USD": 0.02,
            "JPY/USD": 0.005
        }

        result = rank_assets(
            comparison,
            "Latest Daily Return"
        )

        self.assertEqual(
            result,
            [
                ("EUR/USD",0.02),
                ("JPY/USD",0.005),
                ("Gold",-0.01)
            ]
        )

    def test_missing_values_are_excluded(self):

        comparison = {
            "Gold": 0.25,
            "EUR/USD": None,
            "JPY/USD": 0.12
        }

        result = rank_assets(
            comparison,
            "Annualized Volatility"
        )

        self.assertEqual(
            result,
            [
                ("JPY/USD",0.12),
                ("Gold",0.25)
            ]
        )

    def test_empty_comparison(self):

        result = rank_assets(
            {},
            "Annualized Volatility"
        )

        self.assertEqual(result,[])

    def test_rejects_non_rankable_metric(self):

        comparison = {
            "Gold": 2500,
            "EUR/USD": 1.15
        }

        with self.assertRaises(ValueError):
            rank_assets(comparison,"Latest Price")

    def test_rejects_invalid_metric(self):
        with self.assertRaises(ValueError):
            rank_assets({},"Sharpe Ratio")

    def rank_all_volatility_response(self,mock_compare):

        mock_compare.return_value = {
            "Gold": 0.25,
            "EUR/USD": 0.08,
            "JPY/USD": 0.12,
            "STOXX 50": 0.15
        }

        response = get_comparison_response(
            "Rank all assets by volatility"
        )

        self.assertIn("lowest volatility first")
        self.assertIn("Lowest-volatility asset: **EUR/USD**",response)
        self.assertIn("8.00%",response)

        @patch("src.marketmate.compare_assets")
        def test_two_asset_volatility_response(self, mock_compare):

            mock_compare.return_value = {
                "Gold": 0.25,
                "EUR/USD": 0.08
            }

            response = get_comparison_response(
                "Compare gold and EUR/USD by volatility"
            )

            self.assertIn(
                "EUR/USD** has lower annualized volatility",
                response
            )

            self.assertIn("17.00 percentage points", response)

        @patch("src.marketmate.compare_assets")
        def test_drawdown_response(self, mock_compare):

            mock_compare.return_value = {
                "Gold": -0.20,
                "EUR/USD": -0.05
            }

            response = get_comparison_response(
                "Compare gold and EUR/USD by maximum drawdown"
            )

            self.assertIn(
                "less severe maximum drawdown",
                response
            )

        @patch("src.marketmate.compare_assets")
        def test_price_values_are_not_ranked_or_scaled(self, mock_compare):

            mock_compare.return_value = {
                "Gold": 2500.0,
                "EUR/USD": 1.15
            }

            response = get_comparison_response(
                "Compare gold and EUR/USD by price"
            )

            self.assertIn("2,500.0000", response)
            self.assertIn("1.1500", response)
            self.assertIn("not ranked", response)
            self.assertIn("15.00 percentage points", response)

        @patch("src.marketmate.compare_assets")
        def test_observations_are_formatted_as_counts(self, mock_compare):

            mock_compare.return_value = {
                "Gold": 250,
                "EUR/USD": 260
            }

            response = get_comparison_response(
                "Compare gold and EUR/USD by observations"
            )

            self.assertIn("250 observations", response)
            self.assertIn("260 observations", response)
            self.assertIn("not ranked", response)

            
if __name__ == "__main__":
    unittest.main()