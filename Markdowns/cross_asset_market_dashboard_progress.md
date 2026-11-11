# Cross-Asset Market Risk Dashboard --- Project Progress and Workflow

**Project directory:**
`C:\Users\Amoghaya\Desktop\Projects\Personal\cross_asset_market_dashboard`\
**Documentation date:** 29 October 2026\
**Status:** Historical price retrieval and core dashboard metrics are
working for a tested set of instruments. The next planned phase is
visual design and dashboard aesthetics.

------------------------------------------------------------------------

## 1. Project objective

The project is a Python-based cross-asset market risk dashboard built
around LSEG Workspace data. The aim is to retrieve market prices for
several asset classes, transform those observations into a consistent
time series, calculate risk measures, and present the results in a
Streamlit dashboard.

The current tested universe includes:

  -----------------------------------------------------------------------
  Instrument RIC          Instrument category     Price field returned by
                                                  the current loader
  ----------------------- ----------------------- -----------------------
  `EUR=`                  EUR currency quote      `MID_PRICE`

  `JPY=`                  JPY currency quote      `MID_PRICE`

  `XAU=`                  Gold quote              `MID_PRICE`

  `LCOc1`                 Brent crude oil futures `TRDPRC_1`

  `GS.N`                  Goldman Sachs equity    `TRDPRC_1`

  `.STOXX50E`             EURO STOXX 50 index     `TRDPRC_1`

  `.IXIC`                 Nasdaq Composite index  `TRDPRC_1`
  -----------------------------------------------------------------------

This list reflects the instruments tested successfully in the latest
diagnostic run. It should not be interpreted as proof that every
possible instrument or field is available under the current LSEG account
permissions.

## 2. Development environment and tools

-   **Python:** Project-specific virtual environment (`.venv`).
-   **IDE:** Visual Studio Code.
-   **Market data:** LSEG Workspace Python library, imported in the
    project as `refinitiv.data as rd`.
-   **Data processing:** `pandas` and `numpy`.
-   **Dashboard:** `streamlit`.
-   **Charts:** `plotly.express`.
-   **Project layout:** Application/UI code is separated from data
    retrieval and risk calculations under `src/`.

The project has used the `refinitiv.data` package version 1.6.2 during
development. Keep the active interpreter and installed packages
consistent: VS Code should use the project `.venv`, rather than
accidentally running the Anaconda base interpreter or another Python
installation.

### Running the dashboard

From the project directory in PowerShell:

``` powershell
cd "C:\Users\Amoghaya\Desktop\Projects\Personal\cross_asset_market_dashboard"
.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

If activation is unavailable or unnecessary, invoke the virtual
environment's Python directly:

``` powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Use the same interpreter to install packages and run diagnostic scripts.
A folder path such as `.venv\Scripts\` is not itself an activation
command; use `.\.venv\Scripts\Activate.ps1` in PowerShell.

## 3. Project structure and responsibilities

The project has been organized around separating data access, risk
calculations, and presentation.

``` text
cross_asset_market_dashboard/
├── .venv/
├── app.py
├── test_live_data.py
├── src/
│   ├── data_loader.py
│   └── risk_metrics.py
├── data/
│   ├── raw/
│   │   └── sp500_daily_prices.csv
│   └── processed/
│       └── aligned_prices.csv
└── ...
```

The tree is a functional overview, not a guarantee that every listed
file is currently populated or required by the running app.

### `app.py` --- dashboard and user interaction

The Streamlit application is responsible for:

-   Rendering the page and sidebar inputs.
-   Collecting the selected RIC and date range.
-   Opening/reusing an LSEG session through a cached resource function.
-   Calling the data loader when the user clicks **Fetch live data**.
-   Keeping fetched prices and request details in Streamlit session
    state.
-   Passing a selected price series into the risk-metrics function.
-   Displaying headline metrics and charts with Streamlit and Plotly.

The app uses session-state keys such as `live_prices` and
`live_request`. These names must be consistent wherever data is written
to or read from session state.

### `src/data_loader.py` --- data retrieval and normalization

This module contains the market-data loading logic, including
`fetch_live_feed(ric, start_date, end_date)`. Its job is to retrieve
historical daily observations from LSEG and return a clean price series
indexed by date.

The loader now:

1.  Strips and validates the RIC.
2.  Converts the supplied start and end dates into normalized pandas
    timestamps.
3.  Rejects a start date that comes after the end date.
4.  Calls `rd.get_history()` with the requested RIC, daily interval, and
    supplied dates.
5.  Checks that LSEG returned non-empty data.
6.  Looks for a supported price field, rather than assuming every
    instrument returns the same field name.
7.  Uses a date/datetime column when available, or the DataFrame index
    when dates are stored there.
8.  Converts the chosen price values to numeric values.
9.  Removes unusable date/price rows, normalizes dates, sorts the index,
    filters to the requested date range, and removes duplicate dates.
10. Returns a `pandas.Series` named after the RIC, with a date index.

The current candidate price-field names include `TRDPRC_1`, `MID_PRICE`,
`SETTLE`, `TR.PRICECLOSE`, and `PRICE CLOSE`. The loader chooses the
first candidate that matches a returned column after case normalization.
The exact field chosen can differ across instruments.

**Important terminology:** Despite the function name `fetch_live_feed`,
the current implementation calls `get_history()` and retrieves
historical daily observations. It is not yet a real-time streaming feed.
Renaming the function later may make this distinction clearer.

### `src/risk_metrics.py` --- calculations

The `calculate_metrics(prices)` function expects a pandas Series of
prices. The current calculation flow is:

1.  Drop missing prices and sort chronologically.
2.  Calculate simple daily percentage returns using
    `pct_change(fill_method=None)`.
3.  Calculate annualized rolling volatility using a 20-observation
    rolling standard deviation of daily returns multiplied by
    (`\sqrt{252}`{=tex}).
4.  Build a wealth index from daily returns.
5.  Track the running peak of the wealth index.
6.  Calculate drawdown as the wealth index relative to its running peak
    minus one.
7.  Return the metric dictionary, daily returns, rolling volatility, and
    drawdown series for the dashboard to display.

The metric dictionary currently uses these exact, case-sensitive keys:

-   `Observations`
-   `Annualized volatility`
-   `Maximum drawdown`
-   `Latest price`
-   `Latest daily return`

Because the dashboard accesses these values by key, preserve spelling
and capitalization unless both the calculation module and the app are
updated together.

## 4. Methodology followed so far

We have followed an incremental, test-before-integration workflow rather
than building every feature at once.

### Step 1 --- Establish a working local Python environment

-   Created/used a project-specific `.venv`.
-   Diagnosed interpreter-selection and PowerShell activation issues.
-   Resolved the shell execution-policy issue sufficiently to activate
    the environment.
-   Confirmed that required libraries such as `streamlit`, `pandas`, and
    `ipywidgets` were installed in the relevant Python environment at
    different stages of development.
-   Used the project interpreter explicitly when necessary to avoid
    confusion between the virtual environment and Anaconda.

**Why this matters:** Many apparent code errors are actually caused by
running a different interpreter from the one in which packages were
installed.

### Step 2 --- Explore LSEG Workspace access and data fields

-   Opened an LSEG session with `rd.open_session()`.
-   Tested daily historical retrieval using `rd.get_history()`.
-   Investigated `rd.get_data()` and field-based requests, including
    requests involving `TR.PriceClose`.
-   Learned that different instruments can return different fields and
    data layouts.
-   Identified that dates may be represented by the DataFrame index
    rather than a normal `Date` column.
-   Encountered instrument-specific permission errors, including
    `TSCC.QS.UserNotPermission.92000` for `.SPX` and `.DJI` in the
    tested request path.

**Lesson learned:** Do not assume a single field or response layout
works for every asset. Inspect returned columns and the index before
writing general-purpose extraction code. Permission errors should be
diagnosed separately from code errors and market-calendar effects.

### Step 3 --- Diagnose and correct the historical-data loader

The first versions of the loader had assumptions that did not hold for
all instruments:

-   Some date values were hardcoded instead of using the function
    arguments.
-   The code assumed the returned price field would be `TR.PriceClose`.
-   The code assumed a date column existed, even when the dates were
    already in the index.

The loader was revised to accept the supplied RIC and date range, select
a supported returned price field, and derive dates from either a date
column or the index. It now checks for empty results and unusable prices
and returns a consistent Series.

This is an important project milestone: one retrieval function can now
handle several tested instruments with different returned price fields.

### Step 4 --- Test instruments individually before integrating them

A separate `test_live_data.py` script was used to test instruments one
at a time. For each RIC, it printed sample observations, observation
count, date range, missing-value count, and duplicate-date count.
Exceptions were caught per instrument so that one failed request would
not prevent the remaining instruments from being tested.

The latest test succeeded for all seven RICs listed in Section 1. The
returned series had:

-   16 observations for each tested instrument.
-   A date range from 2 October 2026 through 23 October 2026.
-   No missing values in the returned Series.
-   No duplicate dates in the returned index.

The request started on 1 October, but the first usable returned
observation was 2 October. The diagnostic result does not establish why
1 October was absent; this should be checked if that date matters to a
future analysis.

A FutureWarning appeared during the `LCOc1` request. It did not prevent
the data from being returned. It should be monitored, but it was not the
cause of a failed test.

### Step 5 --- Build the risk calculations separately from the UI

The risk calculations were placed in `src/risk_metrics.py` instead of
being embedded directly into `app.py`. This keeps the mathematics easier
to inspect and test, and lets the same function be reused for different
instruments.

The app cleans and sorts the selected price series before passing it
into the calculations. It then displays the headline results and uses
the returned time series for visualizations.

### Step 6 --- Connect the data loader to Streamlit

The app now provides a RIC/date input workflow and a **Fetch live data**
button. The app opens an LSEG session using a function decorated with
`st.cache_resource`, then calls the loader. The returned Series is
stored in session state and subsequently used for metric calculation and
charting.

Session state is important because Streamlit reruns the app script after
many user interactions. Storing the fetched result allows the app to
retain it across reruns rather than requiring a new data request every
time a widget changes.

### Step 7 --- Display useful metrics

The dashboard can now display the key risk outputs produced by
`calculate_metrics`, including:

-   Number of price observations.
-   Annualized volatility.
-   Maximum drawdown.
-   Latest available price.
-   Latest daily return.

The app also has the foundations for time-series visualizations,
including daily returns, rolling volatility, and drawdown, using Plotly.

This is the milestone reached so far: the pipeline can retrieve and
normalize data for several tested instruments and the dashboard can
calculate/display useful metrics. The next phase can therefore focus on
improving information hierarchy and visual presentation, while
preserving the working data and calculation layers.

## 5. Current technical details and caveats

### A. Price-field consistency

The current loader may use `MID_PRICE` for FX and gold, and `TRDPRC_1`
for some equity/index/futures instruments. These fields are not
automatically identical in meaning. Before interpreting cross-asset
returns or comparing risk measures, decide on an appropriate price
convention for each asset class.

For example, a futures workflow may prefer settlement prices for some
analyses, if that field is available and appropriate. Do not silently
substitute fields without documenting the choice.

### B. Currency quote direction

-   `EUR=` is commonly quoted as USD per EUR.
-   `JPY=` is commonly quoted as JPY per USD.

These quote directions differ. If the dashboard eventually compares
returns or builds portfolio exposures across FX pairs, make the quote
convention explicit and invert a series only when the intended analysis
requires it.

### C. Historical data versus streaming data

The current function calls `rd.get_history()` with a daily interval.
This retrieves historical daily observations; it does not establish a
live streaming connection. A true streaming feature would require a
separate implementation and should be treated as a later enhancement.

### D. Sample size and rolling volatility

The latest diagnostic window produced only 16 price observations per
instrument. Daily percentage returns therefore have fewer observations
than the price series, and a 20-return rolling volatility will not yet
have a complete window. A blank or mostly empty 20-day
rolling-volatility chart with this short date range is expected.

For a full 20-return rolling window, at least 21 valid daily prices are
needed. A longer date range is appropriate when testing rolling risk
charts.

### E. Different trading calendars

Markets can have different holidays and observation dates. When multiple
series are combined, align them by date and inspect missing values. An
inner join or dropping every row with any missing value can shorten the
sample substantially, so choose the alignment rule deliberately.

### F. Access permissions

The tested `.SPX` and `.DJI` requests returned
`TSCC.QS.UserNotPermission.92000`. Other instruments succeeded through
the tested history path. This is evidence of an access/request-path
issue for those specific tests, not proof that all S&P 500 or Dow Jones
data is universally unavailable through LSEG.

### G. Historical CSVs and paths

The project has also worked with a local raw-price CSV, including
`data/raw/sp500_daily_prices.csv`, and a planned/used processed-data
location `data/processed/aligned_prices.csv`. When saving CSV files,
provide a full file path including the filename, not just a directory
path. A prior `PermissionError` occurred when a directory path was
passed to `to_csv()` as though it were a file.

## 6. Core calculation definitions

These definitions describe the current implementation at a high level.

### Simple daily return

For price (P_t) on day (t):

\[ r_t = `\frac{P_t}{P_{t-1}}`{=tex} - 1 \]

In pandas, the implementation uses:

``` python
returns = prices.pct_change(fill_method=None).dropna()
```

### Annualized rolling volatility

For a rolling window of daily returns:

\[ `\sigma`{=tex}*{`\mathrm{annualized}`{=tex}} =
`\sigma`{=tex}*{`\mathrm{daily}`{=tex}} `\sqrt{252}`{=tex} \]

The implementation uses a 20-observation rolling standard deviation and
the conventional 252-trading-day annualization factor. This is an
estimate based on the available historical sample, not a forecast or a
guarantee of future risk.

### Wealth index and drawdown

The wealth index compounds the daily return series from a starting
value. The running peak records the highest wealth-index value reached
so far. Drawdown measures the percentage decline from that running peak:

\[ `\mathrm{Drawdown}`{=tex}\_t =
`\frac{W_t}{\max_{s \leq t} W_s}`{=tex} - 1 \]

Maximum drawdown is the minimum value in the drawdown series over the
selected sample. It depends on the chosen time window and the way the
wealth index is initialized.

## 7. Suggested dashboard design direction

The next phase is aesthetics and usability, not rewriting the
functioning data pipeline. A clean market-risk layout could be organized
as follows:

1.  **Header:** dashboard name, selected instrument, date range, and a
    clear data-source/status label.
2.  **Top KPI row:** latest price, latest daily return, annualized
    volatility, maximum drawdown, and observation count.
3.  **Main price chart:** price history with a clear time axis and
    restrained gridlines.
4.  **Risk charts:** daily returns, rolling volatility, and drawdown in
    a logical order.
5.  **Controls:** RIC, date range, and fetch/refresh action grouped
    consistently in a sidebar or compact control section.
6.  **Data-quality context:** last observation date, sample size,
    selected price field where available, and a warning when the sample
    is too short for a rolling metric.

### Visual principles

-   Use a consistent typographic scale and spacing.
-   Keep colors semantically consistent---for example, distinguish
    positive and negative returns clearly and use a separate, restrained
    color for volatility.
-   Avoid excessive borders, unnecessary chart legends, and decorative
    elements that compete with the data.
-   Use consistent decimal/percentage formatting.
-   Label units and quote conventions, especially for FX and
    commodities.
-   Make missing data and insufficient history explicit rather than
    presenting empty charts without explanation.
-   Keep chart styling consistent across instruments so comparisons are
    easier.

These are design recommendations for the next phase, not features
already confirmed as implemented.

## 8. Recommended next steps

### Immediate priority --- dashboard aesthetics

-   Review the current page layout and identify which elements deserve
    the most visual prominence.
-   Establish a coherent color palette, typography, spacing, and chart
    style.
-   Improve the KPI section and chart hierarchy without changing the
    working data path.
-   Add concise explanatory captions and useful empty-state messages.
-   Test the appearance with multiple RICs and date ranges.

### Next --- robust multi-asset view

-   Fetch each selected instrument using the existing loader.
-   Combine Series objects by date into a DataFrame.
-   Inspect alignment and missing observations before deciding how to
    handle them.
-   Calculate per-asset returns and risk measures using a clearly
    documented price convention.
-   Add a correlation matrix only after the date alignment and return
    conventions are settled.

### Then --- quality and reliability

-   Add unit tests for field selection, index/date handling, missing
    values, duplicate dates, and invalid date ranges.
-   Test the app with short and long histories.
-   Provide clear messages for permission errors and empty responses.
-   Consider separating historical retrieval from any future
    streaming-data functionality.
-   Document any assumptions about price fields, FX quote directions,
    annualization, and data calendars.

## 9. Current status summary

  -----------------------------------------------------------------------
  Area                                Status
  ----------------------------------- -----------------------------------
  Project-specific Python environment Set up and used

  LSEG session and historical-data    Tested
  exploration                         

  Generalized historical loader for   Working in latest diagnostics
  tested instruments                  

  Date-index and varying-price-field  Addressed in loader
  handling                            

  Seven-RIC diagnostic test           Passed in latest reported run

  Core risk metrics                   Implemented in `risk_metrics.py`

  Streamlit data-fetch interaction    Integrated

  Headline metric display             Working milestone reached

  Multi-asset aligned matrix and      Next functional step
  cross-asset analysis                

  Dashboard aesthetics and visual     Immediate next priority
  hierarchy                           

  True real-time streaming feed       Not implemented by the current
                                      historical loader
  -----------------------------------------------------------------------

## 10. Working principles for the rest of the project

The workflow that has worked best so far is:

1.  **Inspect before assuming.** Print returned columns, index, types,
    and sample rows when an API response differs from expectations.
2.  **Test one instrument at a time.** Isolate data-access problems
    before combining instruments.
3.  **Normalize at the boundary.** Make the loader return a predictable
    Series so downstream calculations do not need to know every API
    response variation.
4.  **Separate responsibilities.** Keep retrieval, calculations, and
    presentation in different modules.
5.  **Use diagnostics rather than guessing.** Check observation counts,
    date ranges, missing values, and duplicates.
6.  **Distinguish bugs from limitations.** A malformed extraction is a
    code bug; a permission error may be an access limitation; an empty
    rolling window may simply reflect insufficient history.
7.  **Preserve working components.** Improve the UI incrementally
    without destabilizing the data and risk pipeline.
8.  **Document assumptions.** Field selection, quote direction,
    calendars, and sample length affect interpretation and should be
    visible to the developer---and eventually the dashboard user.

------------------------------------------------------------------------

**Milestone achieved:** the dashboard has moved beyond a blank UI and
can display meaningful metrics from historical LSEG price data for a
tested set of instruments. The next phase is to make that working output
look and feel like a polished market-risk application, while continuing
to validate data semantics and cross-asset consistency.
