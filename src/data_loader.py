from pathlib import Path
import pandas as pd
import refinitiv.data as rd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PRICE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "aligned_prices.csv"
)

@st.cache_data(ttl=3600)
def fetch_live_feed(ric,start_date,end_date):
    ric = ric.strip()
    if not ric:
        raise ValueError("Please Enter an Instrument RIC")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    if start > end:
        raise ValueError("Start Date must be on or before End Date")

    #Retrieve daily historical closing prices
    data = rd.get_history(
        universe=[ric],
        interval="1D",
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
    )

    if data is None or data.empty:
        raise ValueError(
            f"LSEG returned no historical data for {ric}"
        )
    
    print("Returned columns:", data.columns.tolist())
    print("Column types:", data.dtypes.to_dict())
    print("Returned index:", data.index.name)
    print(data.head())


    #Identify the returned closing price column
    price_candidates = ["TRDPRC_1","MID_PRICE","SETTLE","TR.PRICECLOSE","PRICE CLOSE"]
    columns_by_name = {
        str(col).strip().upper(): col for col in data.columns
    }

    price_col = next(
        (
            columns_by_name[field] 
            for field in price_candidates
            if field in columns_by_name
        ),
        None,
    )

    print(f"Selected price columns:{price_col}")

    if price_col is None:
        raise ValueError(
            f"No supported price field found for {ric}."
            f"Returned columns: {data.columns.tolist()}"
        )

    #Identify the returned date column
    date_col = next(
        (
            col for col in data.columns
            if str(col).strip().casefold() in {"date","datetime"}
        ),
        None,
    )

    if date_col is not None:
        dates = pd.to_datetime(
            data[date_col],errors="coerce"
        )
    else:
        dates = pd.to_datetime(
            data.index,errors="coerce"
        )

    result = pd.DataFrame({
        "Date":dates,
        "Price":pd.to_numeric(
            data[price_col].to_numpy(),
            errors="coerce"
        ),
    })

    result = result.dropna(subset=["Date","Price"])
    result["Date"] = (
        pd.to_datetime(result["Date"])
        .dt.tz_localize(None)
        .dt.normalize()
    )

    result = result.set_index("Date").sort_index()

    result = result.loc[
        (result.index >= start)
        & (result.index <= end)
    ]

    if result.empty:
        raise ValueError(
            f"No usable closing price could be retained for {ric}."
        )

    #Remove duplicate dates
    result = result[~result.index.duplicated(keep="last")]

    return result["Price"].rename(ric)
