import unittest
import pandas as pd

from src.risk_metrics import calculate_metrics

class TestCalculationMetrics(unittest.TestCase):

    def test_initial_loss_is_recorded_as_drawdown(self):

        prices = pd.Series(
            [100,90],
            index=pd.date_range("2026-01-01",periods=2)
        )

        result = calculate_metrics(prices)

        self.assertAlmostEqual(
            result["metrics"]["Maximum Drawdown"],
            -0.10
        )

    def test_maximum_drawdown_after_recovery(self):

        prices = pd.Series(
            [100,90,100,80],
            index=pd.date_range("2026-01-01",periods=4)
        )

        result = calculate_metrics(prices)

        self.assertAlmostEqual(
            result["metrics"]["Maximum Drawdown"],
            -0.20
        )

    def test_latest_price_and_return(self):

        prices = pd.Series(
            [100, 110, 121],
            index=pd.date_range("2026-01-01", periods=3)
        )

        result = calculate_metrics(prices)

        self.assertEqual(
            result["metrics"]["Latest Price"],
            121
        )

        self.assertAlmostEqual(
            result["metrics"]["Latest Daily Return"],
            0.10
        )

    def test_insufficient_observations(self):

        prices = pd.Series(
            [100],
            index=pd.date_range("2026-01-01", periods=1)
        )

        with self.assertRaises(ValueError):
            calculate_metrics(prices)

if __name__ == "__main__":
    unittest.main()