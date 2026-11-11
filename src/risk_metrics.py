import numpy as np
import pandas as pd

def calculate_metrics(prices):
    prices = prices.dropna().sort_index()

    if len(prices) < 2:
        raise ValueError("Atleast two valid price observations are required")

    returns = prices.pct_change(fill_method=None).dropna()

    if returns.empty:
        raise ValueError("Unable to calculate returns")

    rolling_volatility = (
        returns.rolling(window=20).std() * np.sqrt(252)
    )

    wealth_index = (1+returns).cumprod()
    running_peak = wealth_index.cummax().clip(lower=1.0)
    drawdown = wealth_index / running_peak - 1

    metrics = {
        "Observations":len(prices),
        "Annualized Volatility":(
            returns.std() * np.sqrt(252)
        ),
        "Maximum Drawdown":drawdown.min(),
        "Latest Price":prices.iloc[-1],
        "Latest Daily Return":returns.iloc[-1]
    }

    return {
        "returns":returns,
        "rolling_volatility":rolling_volatility,
        "drawdown":drawdown,
        "metrics":metrics
    }

