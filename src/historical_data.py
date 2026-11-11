import pandas as pd
from src.data_loader import fetch_live_feed

def fetch_multiple_assets(
        ric_list: list,
        start_date: str,
        end_date: str
) -> tuple[pd.DataFrame, dict]:
    #Retrieve and align historical prices for multiple assets

    if not isinstance(ric_list,list) or not ric_list:
        raise ValueError(
            "Provide a non-empty list of RICs."
        )

    if any(not isinstance(ric, str) or not ric.strip() for ric in ric_list):
        raise ValueError(
            "Every RIC must be a non-empty string."
        )

    ric_list = [ric.strip() for ric in ric_list]

    if len(ric_list) != len(set(ric_list)):
        raise ValueError(
            "Duplicate RICs are not allowed."
        )

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    if start > end:
        raise ValueError(
            "Start date must be on or before the end date."
        )

    asset_prices = {}
    failures = {}

    for ric in ric_list:

        try:

            prices = fetch_live_feed(
                ric,
                start_date,
                end_date
            )

            if prices is None or prices.empty:
                raise ValueError("No historical prices returned.")

            asset_prices[ric] = prices.rename(ric)

        except Exception as e:
            failures[ric] = str(e)

    if not asset_prices:
        raise ValueError(
            f"Historical data retrieval failed for all requested assets. "
            f"Failures: {failures}"
        )

    aligned_prices = pd.concat(
        asset_prices.values(),
        axis=1,
        join="outer"
    ).sort_index()

    aligned_prices.index = pd.to_datetime(
        aligned_prices.index
    ).normalize()

    return aligned_prices, failures