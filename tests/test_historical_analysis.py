
import unittest
import numpy as np
import pandas as pd

from src.historical_analysis import (
    calculate_daily_returns,
    calculate_rolling_volatility,
    calculate_corr_matrix,
    identify_stress_periods,
    calculate_regime_statistics,
    calculate_conditional_correlations
)


class TestDailyReturns(unittest.TestCase):

    def setUp(self):
        dates = pd.date_range("2026-01-01", periods=4, freq="D")

        self.prices = pd.DataFrame(
            {
                "Gold": [100, 110, 99, 108.9],
                "EUR/USD": [1.0, 1.1, 1.21, 1.089]
            },
            index=dates
        )

    def test_daily_returns(self):
        returns = calculate_daily_returns(self.prices)

        expected = pd.DataFrame(
            {
                "Gold": [np.nan, 0.10, -0.10, 0.10],
                "EUR/USD": [np.nan, 0.10, 0.10, -0.10]
            },
            index=self.prices.index
        )

        pd.testing.assert_frame_equal(
            returns,
            expected,
            check_exact=False,
            atol=1e-10
        )

    def test_returns_are_sorted_by_date(self):
        prices = self.prices.iloc[::-1]

        returns = calculate_daily_returns(prices)

        self.assertTrue(returns.index.is_monotonic_increasing)

    def test_empty_dataframe(self):
        with self.assertRaises(ValueError):
            calculate_daily_returns(pd.DataFrame())

    def test_duplicate_dates(self):
        prices = self.prices.copy()
        prices.index = [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
            "2026-01-01"
        ]

        with self.assertRaises(ValueError):
            calculate_daily_returns(prices)

    def test_non_positive_prices(self):
        prices = self.prices.copy()
        prices.iloc[1, 0] = 0

        with self.assertRaises(ValueError):
            calculate_daily_returns(prices)


class TestRollingVolatility(unittest.TestCase):

    def setUp(self):
        self.returns = pd.DataFrame(
            {
                "Gold": [0.01, -0.02, 0.03, -0.01, 0.02],
                "EUR/USD": [0.02, 0.01, -0.01, 0.03, -0.02]
            }
        )

    def test_rolling_volatility(self):
        result = calculate_rolling_volatility(
            self.returns,
            window=3
        )

        expected = (
            self.returns
            .rolling(window=3)
            .std()
            * np.sqrt(252)
        )

        pd.testing.assert_frame_equal(result, expected)

    def test_window_validation(self):
        with self.assertRaises(ValueError):
            calculate_rolling_volatility(self.returns, window=1)

    def test_empty_dataframe(self):
        with self.assertRaises(ValueError):
            calculate_rolling_volatility(pd.DataFrame())



class TestCorrelationMatrix(unittest.TestCase):

    def setUp(self):

        self.returns = pd.DataFrame({
            "Asset_A": [0.01, 0.02, 0.03, 0.04, 0.05],
            "Asset_B": [0.02, 0.04, 0.06, 0.08, 0.10],
            "Asset_C": [0.05, 0.03, 0.04, 0.02, 0.01]
        })

    def test_perfect_positive_correlation(self):

        correlation, counts = calculate_corr_matrix(
            self.returns,
            min_observations=3
        )

        self.assertAlmostEqual(
            correlation.loc["Asset_A", "Asset_B"],
            1.0
        )

    def test_observation_counts(self):

        correlation, counts = calculate_corr_matrix(
            self.returns,
            min_observations=3
        )

        self.assertEqual(
            counts.loc["Asset_A", "Asset_B"],
            5
        )

    def test_insufficient_observations(self):

        correlation, counts = calculate_corr_matrix(
            self.returns,
            min_observations=6
        )

        self.assertTrue(
            correlation.loc["Asset_A", "Asset_B"] !=
            correlation.loc["Asset_A", "Asset_B"]
        )

        self.assertEqual(
            counts.loc["Asset_A", "Asset_B"],
            5
        )

    def test_missing_observations(self):

        returns = self.returns.copy()

        returns.loc[0, "Asset_B"] = np.nan

        correlation, counts = calculate_corr_matrix(
            returns,
            min_observations=3
        )

        self.assertEqual(
            counts.loc["Asset_A", "Asset_B"],
            4
        )

    def test_requires_two_assets(self):

        returns = self.returns[["Asset_A"]]

        with self.assertRaises(ValueError):
            calculate_corr_matrix(returns)

    def test_invalid_min_observations(self):

        with self.assertRaises(ValueError):
            calculate_corr_matrix(
                self.returns,
                min_observations=1
            )


class TestStressIdentification(unittest.TestCase):

    def setUp(self):
        self.volatility = pd.Series(
            [0.10, 0.11, 0.12, 0.13, 0.14,
             0.15, 0.16, 0.17, 0.18, 0.50]
        )

    def test_stress_classification(self):

        stress, threshold = identify_stress_periods(
            self.volatility,
            percentile=0.90
        )

        self.assertTrue(stress.iloc[-1])
        self.assertFalse(stress.iloc[0])

    def test_threshold_calculation(self):

        stress, threshold = identify_stress_periods(
            self.volatility,
            percentile=0.90
        )

        expected = self.volatility.quantile(0.90)

        self.assertAlmostEqual(threshold, expected)

    def test_missing_observations(self):

        volatility = self.volatility.copy()
        volatility.iloc[0] = np.nan

        stress, threshold = identify_stress_periods(
            volatility
        )

        self.assertTrue(pd.isna(stress.iloc[0]))
        self.assertTrue(stress.iloc[-1])

    def test_empty_series(self):

        with self.assertRaises(ValueError):
            identify_stress_periods(pd.Series(dtype=float))

    def test_invalid_percentile(self):

        with self.assertRaises(ValueError):
            identify_stress_periods(
                self.volatility,
                percentile=1.5
            )

    def test_negative_volatility(self):

        volatility = self.volatility.copy()
        volatility.iloc[0] = -0.10

        with self.assertRaises(ValueError):
            identify_stress_periods(volatility)

    def test_all_missing_values(self):

        volatility = pd.Series([np.nan, np.nan, np.nan])

        with self.assertRaises(ValueError):
            identify_stress_periods(volatility)



class TestRegimeStatistics(unittest.TestCase):

    def setUp(self):

        self.returns = pd.DataFrame({
            "Gold": [0.01, 0.02, -0.01, 0.03, 0.04, -0.02],
            "EUR/USD": [0.02, -0.01, 0.01, 0.02, -0.02, 0.01]
        })

        self.stress_periods = pd.Series(
            [False, False, True, True, False, True]
        )

    def test_observation_counts(self):

        results = calculate_regime_statistics(
            self.returns,
            self.stress_periods
        )

        self.assertEqual(
            results["Gold"]["stress"]["observations"],
            3
        )

        self.assertEqual(
            results["Gold"]["non_stress"]["observations"],
            3
        )

    def test_average_daily_return(self):

        results = calculate_regime_statistics(
            self.returns,
            self.stress_periods
        )

        expected = np.mean([-0.01, 0.03, -0.02])

        self.assertAlmostEqual(
            results["Gold"]["stress"]["average_daily_return"],
            expected
        )

    def test_annualized_volatility(self):

        results = calculate_regime_statistics(
            self.returns,
            self.stress_periods
        )

        expected = (
            pd.Series([-0.01, 0.03, -0.02]).std()
            * np.sqrt(252)
        )

        self.assertAlmostEqual(
            results["Gold"]["stress"]["annualized_volatility"],
            expected
        )

    def test_missing_returns(self):

        returns = self.returns.copy()
        returns.loc[2, "Gold"] = np.nan

        results = calculate_regime_statistics(
            returns,
            self.stress_periods
        )

        self.assertEqual(
            results["Gold"]["stress"]["observations"],
            2
        )

    def test_incompatible_indexes(self):

        stress = self.stress_periods.copy()
        stress.index = range(1, 7)

        with self.assertRaises(ValueError):
            calculate_regime_statistics(
                self.returns,
                stress
            )

    def test_unclassified_observations(self):

        stress = self.stress_periods.copy().astype("boolean")
        stress.iloc[0] = pd.NA

        with self.assertRaises(ValueError):
            calculate_regime_statistics(
                self.returns,
                stress
            )

    def test_single_observation_volatility(self):

        returns = pd.DataFrame({
            "Gold": [0.01, 0.02]
        })

        stress = pd.Series([True, False])

        results = calculate_regime_statistics(
            returns,
            stress
        )

        self.assertIsNone(
            results["Gold"]["stress"]["annualized_volatility"]
        )


class TestConditionalCorrelations(unittest.TestCase):

    def setUp(self):

        self.returns = pd.DataFrame({
            "Asset_A": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06],
            "Asset_B": [0.02, 0.04, 0.06, 0.08, 0.10, 0.12],
            "Asset_C": [0.06, 0.04, 0.05, 0.03, 0.02, 0.01]
        })

        self.stress_periods = pd.Series(
            [True, True, True, False, False, False]
        )

    def test_stress_observation_counts(self):

        results = calculate_conditional_correlations(
            self.returns,
            self.stress_periods,
            min_observations=2
        )

        counts = results["stress"]["observation_counts"]

        self.assertEqual(
            counts.loc["Asset_A", "Asset_B"],
            3
        )

    def test_non_stress_observation_counts(self):

        results = calculate_conditional_correlations(
            self.returns,
            self.stress_periods,
            min_observations=2
        )

        counts = results["non_stress"]["observation_counts"]

        self.assertEqual(
            counts.loc["Asset_A", "Asset_B"],
            3
        )

    def test_perfect_stress_correlation(self):

        results = calculate_conditional_correlations(
            self.returns,
            self.stress_periods,
            min_observations=2
        )

        correlation = results["stress"]["correlation_matrix"]

        self.assertAlmostEqual(
            correlation.loc["Asset_A", "Asset_B"],
            1.0
        )

    def test_incompatible_indexes(self):

        stress = self.stress_periods.copy()
        stress.index = range(1, 7)

        with self.assertRaises(ValueError):
            calculate_conditional_correlations(
                self.returns,
                stress
            )

    def test_unclassified_observations(self):

        stress = self.stress_periods.copy().astype("boolean")
        stress.iloc[0] = pd.NA

        with self.assertRaises(ValueError):
            calculate_conditional_correlations(
                self.returns,
                stress
            )



if __name__ == "__main__":
    unittest.main()
