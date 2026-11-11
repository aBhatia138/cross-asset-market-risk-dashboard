import numpy as np
import pandas as pd

TRADING_DAYS = 252

def calculate_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    #Calculate daily percentage returns from asset prices

    if not isinstance(prices,pd.DataFrame):
        raise TypeError(
            "Prices must be a pandas DataFrame."
        )

    if prices.empty:
        raise ValueError(
            "Price DataFrame cannot be empty."
        )

    prices = prices.copy()

    prices.index = pd.to_datetime(prices.index)

    if not prices.index.is_unique:
        raise ValueError(
            "Price DataFrame contains duplicate dates."
        )

    prices = prices.sort_index()

    prices = prices.apply(pd.to_numeric,errors="coerce")

    if(prices.dropna(how="all") <= 0).any().any():
        raise ValueError(
            "Asset prices must be postitive."
        )

    returns = prices.pct_change(fill_method=None)

    return returns.replace([np.inf,-np.inf], np.nan)

def calculate_rolling_volatility(
    returns: pd.DataFrame,
    window: int = 21
) -> pd.DataFrame:

    #Calculate annualized rolling volatility for each asset
    if not isinstance(returns,pd.DataFrame):
        raise TypeError(
            "Returns must be a pandas dataframe."
        )

    if returns.empty:
        raise ValueError(
            "Returns dataframe cannot be empty."
        )

    if not isinstance(window,int) or isinstance(window,bool) or window < 2:
        raise ValueError(
            "Window must be an integer of length atleast 2."
        )

    rolling_volatility = (
        returns
        .rolling(window=window,min_periods=window)
        .std()
        * np.sqrt(TRADING_DAYS)
    )

    return rolling_volatility

def calculate_corr_matrix(
        returns: pd.DataFrame,
        # min_observations: int=30,
        min_observations: int = 30,
) -> tuple[pd.DataFrame,pd.DataFrame]:
    #Calculate pairwise Pearson correlations between asset returns.
    if not isinstance(returns,pd.DataFrame):
        raise TypeError(
            "Returns must be a pandas DataFrame."
        )

    if returns.empty:
        raise ValueError(
            "Returns DataFrame cannot be empty."
        )

    if (not isinstance(min_observations, int)
        or isinstance(min_observations, bool)
        or min_observations < 2):

        raise ValueError(
            "Minimum observations must be an integer of length atleast 2"
        )

    if returns.shape[1] < 2:
        raise ValueError(
            "Atleast two assets are required."
        )

    returns = returns.copy()
    returns = returns.apply(pd.to_numeric, errors="coerce")

    if not returns.columns.is_unique:
        raise ValueError(
            "Asset columns must be unique."
        )

    if not returns.index.is_unique:
        raise ValueError(
            "Return DataFrame contains duplicate dates."
        )

    returns = returns.replace([np.inf, -np.inf], np.nan)

    assets = returns.columns

    correlation_matrix = pd.DataFrame(
        np.nan,
        index=assets,
        columns=assets
    )

    observation_counts = pd.DataFrame(
        0,
        index=assets,
        columns=assets
    )

    for asset_1 in assets:
        for asset_2 in assets:

            paired_returns = returns[[asset_1, asset_2]].dropna()

            observation_count = len(paired_returns)

            observation_counts.loc[asset_1, asset_2] = observation_count

            if observation_count < min_observations:
                continue

            correlation = paired_returns.corr(method="pearson").iloc[0,1]

            correlation_matrix.loc[asset_1, asset_2] = correlation

    return correlation_matrix, observation_counts

def identify_stress_periods(
        rolling_volatility: pd.Series,
        percentile: float=0.90
) -> tuple[pd.Series, float]:
    #Identify historical stress periods using a rolling-volatility threshold.

    if not isinstance(rolling_volatility, pd.Series):
        raise TypeError(
            "Rolling volatility must be a pandas Series."
        )

    if rolling_volatility.empty:
        raise ValueError(
            "Rolling volatility cannot be empty."
        )

    if not isinstance(percentile, (int, float)) or isinstance(percentile, bool):
        raise TypeError(
            "Percentile must be numeric."
        )

    if not 0 < percentile < 1:
        raise ValueError(
            "Percentile must be between 0 and 1."
        )

    volatility = pd.to_numeric(
        rolling_volatility,
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

    valid_volatility = volatility.dropna()

    if valid_volatility.empty:
        raise ValueError(
            "No valid volaitlity observations available."
        )

    if (valid_volatility < 0).any():
        raise ValueError("Volatility cannot be negative.")

    threshold = valid_volatility.quantile(percentile)

    stress_periods = pd.Series(
        pd.NA,
        index=volatility.index,
        dtype="boolean"
    )

    stress_periods.loc[valid_volatility.index] = (
        valid_volatility > threshold
    )

    return stress_periods, float(threshold)


def calculate_regime_statistics(
        returns: pd.DataFrame,
        stress_periods: pd.Series
) -> dict:
    #Calculate return and volatility statistics for stress 
    # and non-stress regimes
    if not isinstance(returns, pd.DataFrame):
        raise TypeError("Returns must be a pandas DataFrame.")

    if not isinstance(stress_periods, pd.Series):
        raise TypeError("Stress periods must be a pandas Series.")

    if returns.empty:
        raise ValueError("Returns DataFrame cannot be empty.")

    if stress_periods.empty:
        raise ValueError("Stress classification cannot be empty.")

    if not returns.index.is_unique:
        raise ValueError("Returns contain duplicate dates.")

    if not stress_periods.index.is_unique:
        raise ValueError("Stress classification contains duplicate dates.")

    if not returns.columns.is_unique:
        raise ValueError("Asset columns must be unique.")

    if not returns.index.equals(stress_periods.index):
        raise ValueError(
            "Returns and stress classifications must have identical indexes."
        )

    if stress_periods.isna().any():
        raise ValueError(
            "Stress classifications contain unclassified observations."
        )

    if not stress_periods.isin([True, False]).all():
        raise ValueError(
            "Stress classifications must contain only Boolean values."
        )

    returns = returns.apply(pd.to_numeric, errors="coerce")

    returns = returns.replace([np.inf, -np.inf], np.nan)

    results = {}

    regimes = {
        "stress": stress_periods == True,
        "non_stress": stress_periods == False
    }

    for asset in returns.columns:

        results[asset] = {}

        for regime_name, regime_mask in regimes.items():

            regime_returns = returns.loc[regime_mask, asset].dropna()

            observations = len(regime_returns)

            if observations == 0:
                average_return = None
                annualized_volatility = None

            else:
                average_return = float(regime_returns.mean())

                if observations >= 2:
                    annualized_volatility = float(
                        regime_returns.std() * np.sqrt(TRADING_DAYS)
                    )
                else:
                    annualized_volatility = None

            results[asset][regime_name] = {
                "observations": observations,
                "average_daily_return": average_return,
                "annualized_volatility": annualized_volatility
            }

    return results


def calculate_conditional_correlations(
    returns: pd.DataFrame,
    stress_periods: pd.Series,
    # min_observations: int = 30
    min_observations: int = 30,
) -> dict:
    
    #Calculate pairwise asset correlations separately during
    #stress and non-stress periods.

    if not isinstance(returns, pd.DataFrame):
        raise TypeError("Returns must be a pandas DataFrame.")

    if not isinstance(stress_periods, pd.Series):
        raise TypeError("Stress periods must be a pandas Series.")

    if returns.empty:
        raise ValueError("Returns DataFrame cannot be empty.")

    if not returns.index.is_unique:
        raise ValueError("Returns contain duplicate dates.")

    if not returns.columns.is_unique:
        raise ValueError("Asset columns must be unique.")

    if not returns.index.equals(stress_periods.index):
        raise ValueError("Returns and stress classifications must have identical indexes.")

    if stress_periods.isna().any():
        raise ValueError("Stress classifications contain unclassified observations.")

    if not stress_periods.isin([True, False]).all():
        raise ValueError("Stress classifications must contain only Boolean values.")

    results = {}

    regimes = {
        "stress": stress_periods == True,
        "non_stress": stress_periods == False
    }

    for regime_name, regime_mask in regimes.items():

        regime_returns = returns.loc[regime_mask]

        correlation, counts = calculate_corr_matrix(
            regime_returns,
            min_observations=min_observations
        )

        results[regime_name] = {
            "correlation_matrix": correlation,
            "observation_counts": counts
        }

    return results






