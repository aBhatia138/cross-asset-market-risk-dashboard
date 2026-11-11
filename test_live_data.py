import refinitiv.data as rd
from src.data_loader import fetch_live_feed
# import lseg.data as ld

rics = ["EUR=","JPY=","XAU=","LCOc1","GS.N",".STOXX50E",".IXIC"]

rd.open_session()

try:
    for ric in rics:
        try:
            instrument_info = fetch_live_feed(
                ric,
                start_date="2026-10-01",
                end_date="2026-10-23",
            )

            print(instrument_info.head())
            print("\nNumber of observations:", len(instrument_info))
            print("\nDate range:", instrument_info.index.min(), "to", instrument_info.index.max())
            print("First date:", instrument_info.index.min())
            print("Last date:", instrument_info.index.max())
            print("Missing values:", instrument_info.isna().sum())
            print("Duplicate dates:", instrument_info.index.duplicated().sum())
            print("-------------------------------------------------\n\n\n")

        except Exception as e:
            print(f"\n{ric}: FAILED")
            print(type(e).__name__,str(e))

finally:
    rd.close_session()
