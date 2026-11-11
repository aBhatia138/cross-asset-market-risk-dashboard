import os
import unittest 

import pandas as pd

from src.lseg_session import open_lseg_session
from src.historical_data import fetch_multiple_assets

from src.historical_analysis import (
    calculate_daily_returns,
    calculate_corr_matrix,
    calculate_rolling_volatility,
    identify_stress_periods,
    calculate_regime_statistics,
    calculate_conditional_correlations
)

@unittest.skipUnless(
    os.getenv("RUN_LSEG_INTEGRATION") == "1",
    "Set RUN_LSEG_INTEGRATION=1 to run live LSEG tests."
)

class TestLiveHistoricalData(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        #Initialize or resue the cached LSEG session once
        cls.session = open_lseg_session()

        cls.rics = [
            "XAU=",
            "JPY=",
            ".STOXX50E",
            "EUR="
        ]

        cls.start_date = "2025-11-08"
        cls.end_date = "2026-11-08"

    def test_multi_asset_historical_retrieval(self):

        prices, failures = fetch_multiple_assets(
            self.rics,
            self.start_date,
            self.end_date
        )

        # Calculate daily returns
        returns = calculate_daily_returns(prices)

        # Calculate cross-asset correlations
        correlation_matrix, observation_counts = calculate_corr_matrix(returns)

        print("\n========== DAILY RETURNS ==========")
        print(returns.head())

        print("\n========== CORRELATION MATRIX ==========")
        print(correlation_matrix)

        print("\n========== PAIRWISE OBSERVATION COUNTS ==========")
        print(observation_counts)

        # --------------------------------------------------
        # STRESS REGIME ANALYSIS
        # --------------------------------------------------

        # Step 1: Calculate 21-day rolling annualized volatility
        rolling_volatility = calculate_rolling_volatility(
            returns,
            window=21
        )

        # Step 2: Classify stress periods using Euro STOXX 50 volatility
        stress_periods, stress_threshold = identify_stress_periods(
            rolling_volatility[".STOXX50E"],
            percentile=0.80
        )

        # Step 3: Remove dates where rolling volatility is unavailable
        # (the first 20 observations cannot have a full 21-day window)
        classified_stress = stress_periods.dropna().astype(bool)

        classified_returns = returns.loc[classified_stress.index]

        # Step 4: Calculate statistics for each regime
        regime_statistics = calculate_regime_statistics(
            classified_returns,
            classified_stress
        )

        # Step 5: Calculate conditional correlations
        conditional_correlations = calculate_conditional_correlations(
            classified_returns,
            classified_stress,
            min_observations=30
        )

        # --------------------------------------------------
        # DISPLAY RESULTS
        # --------------------------------------------------

        print("\n========== STRESS REGIME ANALYSIS ==========")

        print(f"Stress volatility threshold: {stress_threshold:.4f}")
        print(f"Stress observations: {classified_stress.sum()}")
        print(f"Non-stress observations: {(~classified_stress).sum()}")

        print("\n========== REGIME STATISTICS ==========")
        print(regime_statistics)

        print("\n========== STRESS PERIOD CORRELATIONS ==========")
        print(
            conditional_correlations["stress"]["correlation_matrix"]
        )

        print("\n========== NON-STRESS PERIOD CORRELATIONS ==========")
        print(
            conditional_correlations["non_stress"]["correlation_matrix"]
        )

        print("\n========== STRESS CORRELATION OBSERVATION COUNTS ==========")
        print(
            conditional_correlations["stress"]["observation_counts"]
        )

        print("\n========== NON-STRESS CORRELATION OBSERVATION COUNTS ==========")
        print(
            conditional_correlations["non_stress"]["observation_counts"]
        )

        # Basic validation
        self.assertIsInstance(rolling_volatility, pd.DataFrame)
        self.assertIsInstance(classified_stress, pd.Series)
        self.assertIsInstance(regime_statistics, dict)
        self.assertIsInstance(conditional_correlations, dict)

        self.assertGreater(classified_stress.sum(), 0)
        self.assertGreater((~classified_stress).sum(), 0)

        self.assertIsInstance(returns, pd.DataFrame)
        self.assertIsInstance(correlation_matrix, pd.DataFrame)
        self.assertIsInstance(observation_counts, pd.DataFrame)

        self.assertEqual(correlation_matrix.shape, (4, 4))
        self.assertEqual(observation_counts.shape, (4, 4))

        #Atleast one instrument must have been retrieved
        self.assertIsInstance(prices,pd.DataFrame)
        self.assertFalse(prices.empty)

        print("\n\n========== LSEG DATA COVERAGE ==========")

        for ric in self.rics:
            if ric not in prices.columns:
                print(f"\n{ric}: RETRIEVAL FAILED")
                print(f"Reason: {failures.get(ric, 'Unknown error')}")
                continue

            series = prices[ric].dropna()

            if series.empty:
                print(f"\n{ric}: No valid observations")
                continue

            print(f"\nInstrument: {ric}")
            print(f"Observations: {len(series)}")
            print(f"First observation: {series.index.min()}")
            print(f"Last observation: {series.index.max()}")
            print(f"Missing observations: {prices[ric].isna().sum()}")

        print("\n========== RETRIEVAL FAILURES ==========")

        for ric, reason in failures.items():
            print(f"{ric}: {reason}")

        print("\n========== ALIGNED PRICE DATA ==========")
        print(prices.head())
        print(prices.tail())

        #Atleast one instrument must have enough observations
        #to calculate daily returns

        usable_assets = (
            prices.count() >= 2
        ).sum()

        self.assertGreaterEqual(
            usable_assets,
            1,
            "No instrument has enough observations to calculate returns."
        )

if __name__ == "__main__":
    unittest.main()