from src.marketmate import (get_asset_snapshot,
                            compare_assets,
                            rank_assets)

from datetime import date
import pandas as pd

from src.historical_data import fetch_multiple_assets
from src.data_loader import fetch_live_feed

from src.lseg_session import open_lseg_session

from src.historical_analysis import (
    calculate_daily_returns,
    calculate_rolling_volatility,
    calculate_corr_matrix,
    identify_stress_periods,
    calculate_regime_statistics,
    calculate_conditional_correlations
)

#Only these instruments are supported by the independent asset tool
SUPPORTED_RICS = [
    "XAU=",
    "EUR=",
    "JPY=",
    ".STOXX50E"
]

ASSET_MAPPING = {
    "XAU=": "Gold",
    "EUR=": "EUR/USD",
    "JPY=": "JPY/USD",
    ".STOXX50E": "Euro STOXX 50"
}

#Maps approved tool names to actual Python functions
TOOLFUNCTIONS = {
    "get_asset_snapshot": get_asset_snapshot 
}

def clean_metrics(metrics: dict) -> dict:
    #Convert numpy scalar values into JSON-serializable values

    return {
        key:value.item() if hasattr(value,"item") else value 
        for key, value in metrics.items()
    }

def validate_date_range(start_date, end_date):
    """
    Validate date inputs and ensure start_date <= end_date.
    Returns normalized date strings.
    """

    if not isinstance(start_date, str) or not isinstance(end_date, str):
        raise ValueError("Dates must be strings in YYYY-MM-DD format.")

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("Invalid date. Use YYYY-MM-DD format.")

    if start > end:
        raise ValueError("Start date must be on or before end date.")

    if start.isoformat() != start_date or end.isoformat() != end_date:
        raise ValueError(
            "Dates must be in YYYY-MM-DD format."
        )

    return start.isoformat(), end.isoformat()


def parse_selected_rics(selected_rics):
    """
    Convert a comma-separated RIC string into a validated list.
    """

    if not isinstance(selected_rics, str):
        raise ValueError("Selected assets must be a comma-separated string.")

    rics = [ric.strip() for ric in selected_rics.split(",")]

    if any(not ric for ric in rics):
        raise ValueError("One or more asset identifiers are empty.")

    if len(rics) < 2:
        raise ValueError("At least two assets must be selected.")

    if len(rics) != len(set(rics)):
        raise ValueError("Duplicate assets are not allowed.")

    if any(ric not in SUPPORTED_RICS for ric in rics):
        raise ValueError("One or more unsupported RICs were supplied.")

    return rics


def clean_value(value):
    """Convert Pandas and NumPy scalar values into JSON-safe values."""

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    return value


def dataframe_to_dict(dataframe):
    """Convert a DataFrame into a JSON-serializable nested dictionary."""

    return {
        str(index): {
            str(column): clean_value(value)
            for column, value in row.items()
        }
        for index, row in dataframe.iterrows()
    }

def execute_tool(
    tool_name: str,
    arguments: dict,
    dashboard_context: dict | None = None
) -> dict:

    #Validate the tool name
    if tool_name not in [
        "get_asset_snapshot",
        "get_dashboard_snapshot",
        "compare_assets",
        "rank_assets",
        "get_historical_volatility",
        "get_cross_asset_correlations",
        "get_stress_regime_analysis"
    ]:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }

    #Validate the argument structure
    if not isinstance(arguments, dict):
        return {
            "success": False,
            "error": "Tool arguments must be a dictionary."
        }

    if tool_name == "get_asset_snapshot":

        #The asset tool must receive exactly one argument
        if set(arguments.keys()) != {"ric"}:
            return {
                "success": False,
                "error": "Expected only one argument: ric."
            }

        ric = arguments.get("ric")

        #Validate RIC types
        if not isinstance(ric, str):
            return {
                "success": False,
                "error": "RIC must be a string."
            }

        #Remove accidental leading or trailing whitespaces
        ric = ric.strip()

        #validate supported instrument
        if ric not in SUPPORTED_RICS:
            return {
                "success": False,
                "error": f"Unsupported instrument RIC: {ric}"
            }

        try:
            result = get_asset_snapshot(ric)
            metrics = result.get("metrics")

            if not isinstance(metrics, dict):
                raise ValueError(
                    "Invalid metrics returned by MarketMate."
                )

            return {
                "success": True,
                "tool": tool_name,
                "ric": ric,
                "metrics": clean_metrics(metrics)
            }

        except Exception as e:

            print(
                f"Tool execution failed: {type(e).__name__}: {e}"
            )

            return {
                "success": False,
                "error": f"Unable to retrive data for {ric}"
            }

    if tool_name == "get_dashboard_snapshot":

        #This tool must receive no arguments
        if arguments != {}:
            return {
                "success": False,
                "error": "Dashboard snapshot requires no arguments"
            }

        #Check whether dashboard data is available 
        if not isinstance(dashboard_context, dict):
            return {
                "success": False,
                "error": "No dashboard data is currently available."
            }

        #Validate the required dashboard context fields
        required_fields = {
            "ric",
            "start_date",
            "end_date",
            "first_observation",
            "last_observation",
            "metrics"
        }

        if not required_fields.issubset(dashboard_context.keys()):
            return {
                "success": False,
                "error": "Dashboard context is incomplete."
            }

        ric = dashboard_context["ric"]
        metrics = dashboard_context["metrics"]

        if not isinstance(ric, str) or not ric.strip():
            return {
                "success": False,
                "error": "Invalid dashboard metrics."
            }

        if not isinstance(metrics,dict):
            return {
                "success": False,
                "error": "Dashboard metrics must be a dictionary."
            }

        return {
            "success": True,
            "tool": tool_name,
            "ric": ric,
            "date_range": {
                "start": dashboard_context["start_date"],
                "end": dashboard_context["end_date"]
            },
            "first_observation": dashboard_context["first_observation"],
            "last_observation": dashboard_context["last_observation"],
            "metrics": clean_metrics(metrics)
        }

    if tool_name == "compare_assets":
        #Validate the supplied arguments
        if set(arguments.keys()) != {
            "metric_name",
            "selected_assets"
        }:
            return {
                "success": False,
                "error": "Expected metric_name and selected_assets"
            }

        metric_name = arguments["metric_name"]
        selected_rics = arguments["selected_assets"]

        if not isinstance(metric_name,str):
            return {
                "success": False,
                "error": "Metric name must be a string."
            }

        valid_metrics = [
            "Observations",
            "Annualized Volatility",
            "Maximum Drawdown",
            "Latest Price",
            "Latest Daily Return"
        ]

        if metric_name not in valid_metrics:
            return {
                "success": False,
                "error": "Unsupported comparison metric."
            }

        if not isinstance(selected_rics,str):
            return {
                "success": False,
                "error": "Selected assets must be a comma-separated string."
            }

        #Convert the string into a list of RICs
        selected_rics = [
            ric.strip()
            for ric in selected_rics.split(",")
        ]

        #Reject empty entries
        if any(not ric for ric in selected_rics):
            return {
                "success": False,
                "error": "One or more asset identifiers are empty."
            }

        if len(selected_rics) < 2:
            return {
                "success": False,
                "error": "Select atleast two assets for comparison."
            }

        if len(set(selected_rics)) != len(selected_rics):
            return {
                "success": False,
                "error": "Duplicate assets are not allowed."
            }

        if any(
            not isinstance(ric,str) or ric not in SUPPORTED_RICS
            for ric in selected_rics
        ):
            return {
                "success": False,
                "error": "One or more unsupported RICs were supplied."
            }

        #Convert the RIC list into dictionary expected by compare_assets()
        selected_assets = {
            ASSET_MAPPING[ric]: {"ric":ric}
            for ric in selected_rics
        }

        try:
            comparison = compare_assets(
                metric_name,
                selected_assets
            )

            return {
                "success": True,
                "tool": tool_name,
                "metric_name": metric_name,
                "comparison": clean_metrics(comparison)
            }

        except Exception as e:
            print(f"Comparsion tool failed: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": "Unable to compare the selected assets."
            }

    if tool_name == "rank_assets":

        if set(arguments.keys()) != {
            "metric_name",
            "selected_assets"
        }:
            return {
                "success": False,
                "error": "Expected metric_name and selected_assets."
            }

        metric_name = arguments["metric_name"]
        selected_rics = arguments["selected_assets"]

        if not isinstance(metric_name,str):
            return {
                "success": False,
                "error": "Metric name must be a string."
            }

        rankable_metrics = [
            "Annualized Volatility",
            "Maximum Drawdown",
            "Latest Daily Return"
        ]

        if metric_name not in rankable_metrics:
            return {
                "success": False,
                "error": "Unsupported ranking metric."
            }

        if not isinstance(selected_rics,str):
            return {
                "success": False,
                "error": "Selected assets must be a comma-separated string."
            }

        #Convert the string into a list of RICs
        selected_rics = [
            ric.strip()
            for ric in selected_rics.split(",")
        ]

        #Reject empty entries
        if any(not ric for ric in selected_rics):
            return {
                "success": False,
                "error": "One or more asset identifiers are empty."
            }

        if len(selected_rics) < 2:
            return {
                "success": False,
                "error": "Select atleast two assets for ranking."
            }

        if len(set(selected_rics)) != len(selected_rics):
            return {
                "success": False,
                "error": "Duplicate assets are not allowed."
            }

        if any(
            not isinstance(ric,str) or ric not in SUPPORTED_RICS
            for ric in selected_rics
        ):
            return {
                "success": False,
                "error": "One or more unsupported RICs were supplied."
            }

        selected_assets = {
            ASSET_MAPPING[ric]: {"ric":ric}
            for ric in selected_rics
        }

        try:
            comparison = compare_assets(
                metric_name,
                selected_assets
            )

            ranking = rank_assets(
                comparison,
                metric_name
            )

            return {
                "success": True,
                "tool": tool_name,
                "metric_name": metric_name,
                "ranking": [
                    {
                        "asset": asset,
                        "value": value.item() if hasattr(value,"item")
                        else value
                    }
                    for asset, value in ranking
                ]
            }

        except Exception as e:
            print(f"Ranking tool failed: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": "Unable to rank the selected assets."
            }

    if tool_name == "get_historical_volatility":

        #validate the exact argument structure
        required_arguments = {
            "ric",
            "start_date",
            "end_date"
        }

        optional_arguments = {"window"}

        if (
            not required_arguments.issubset(arguments.keys()) 
            or not set(arguments.keys()).issubset(
                required_arguments | optional_arguments
            )
        ):
            return {
                "success": False,
                "error": (
                    "Expected ric, start_date, end_date "
                    "and optional window. "
                )
            }

        ric = arguments["ric"]
        start_date = arguments["start_date"]
        end_date = arguments["end_date"]
        window = arguments.get("window",21)

        #validate RIC
        if not isinstance(ric, str) or ric.strip() not in SUPPORTED_RICS:
            return {
                "success": False,
                "error": "Unsupported instrument RIC"
            }

        ric = ric.strip()

        #Validate window
        if (
            isinstance(window,bool)
            or not isinstance(window,int)
            or window < 2
        ):
            return {
                "success": False,
                "error": "Window must be an integer >= 2. "
            }

        #Validate the date range
        try:
            start_date, end_date = validate_date_range(
                start_date,
                end_date
            )

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

        try:
            #Retrieve historical prices
            open_lseg_session()

            prices = fetch_live_feed(
                ric,
                start_date,
                end_date
            )

            if prices is None or prices.empty:
                raise ValueError(
                    "No historical prices returned. "
                )

            #Calculate daily returns 
            returns = calculate_daily_returns(
                prices.to_frame(name=ric)
            )

            #Calculate rolling annualized volatility
            rolling_volatility = calculate_rolling_volatility(
                returns,
                window=window
            )

            #Extract the selected instrument's volatility series
            volatility = rolling_volatility[ric].dropna()

            if volatility.empty:
                raise ValueError(
                    "Insufficient observations for rolling volatility. "
                )

            return {
                "success": True,
                "tool": tool_name,
                "ric": ric,
                "asset": ASSET_MAPPING[ric],
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "window": window,
                "observations": len(volatility),
                "latest_annualized_volatility": float(
                    volatility.iloc[-1]
                ),
                "rolling_volatility": {
                    str(index.date()): float(value)
                    for index, value in volatility.items()
                }
            }

        except Exception as e:
            print(
                f"Historical volatility tool failed: "
                f"{type(e).__name__}: {e}"

            )

            return {
                "success": False,
                "error": (
                    f"Unable to calculate historical volatility. "
                    f"for {ric}. "
                )
            }

    if tool_name == "get_cross_asset_correlations":

        required_arguments = {
            "selected_assets",
            "start_date",
            "end_date"
        }

        optional_arguments = {"min_observations"}

        #Validate argument structure
        if (
            not required_arguments.issubset(arguments.keys())
            or not set(arguments.keys()).issubset(
                required_arguments | optional_arguments
            )
        ):
            return {
                "success": False,
                "error": (
                    "Expected selected_assets, start_date, end_date "
                    "and optional min_observations. "
                )
            }

        #Validate selected instruments 
        try:
            selected_rics = parse_selected_rics(
                arguments["selected_assets"]
            )

        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }

        #Validate dates
        try:
            start_date, end_date = validate_date_range(
                arguments["start_date"],
                arguments["end_date"]
            )

        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }

        min_observations = arguments.get("min_observations",30)

        if (
            isinstance(min_observations,bool)
            or not isinstance(min_observations,int)
            or min_observations < 2
        ):
            return {
                "success": False,
                "error": "min_observations must be an integer of at least 2. "
            }

        try:
            #Retrieve and align historical prices
            open_lseg_session()

            prices, failures = fetch_multiple_assets(
                selected_rics,
                start_date,
                end_date
            )

            if prices.shape[1] < 2:
                raise ValueError(
                    "At least two assets must have successfully "
                    "retrieved historical prices."
                )

            #Calculate daily returns
            returns = calculate_daily_returns(prices)

            #Calculate correlation matrix and observation counts
            correlation_matrix, observation_counts = calculate_corr_matrix(
                returns,
                min_observations=min_observations
            )

            return {
                "success": True,
                "tool": tool_name,
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "assets": [
                    {
                        "ric": ric,
                        "name": ASSET_MAPPING[ric]
                    }
                    for ric in prices.columns
                ],
                "min_observations": min_observations,
                "correlation_matrix": dataframe_to_dict(
                    correlation_matrix
                ),
                "observation_counts": dataframe_to_dict(
                    observation_counts
                ),
                "failures": failures
            }

        except Exception as e:

            print(
                f"Cross-asset correlation tool failed: "
                f"{type(e).__name__}: {e}"
            )

            return {
                "success": False,
                "error": (
                    "Unable to calculate cross-asset correlations."
                )
            }

    
    if tool_name == "get_stress_regime_analysis":

        required_arguments = {
            "selected_assets",
            "stress_ric",
            "start_date",
            "end_date"
        }

        optional_arguments = {
            "window",
            "percentile",
            "min_observations"
        }

        # Validate the argument names.
        if (
            not required_arguments.issubset(arguments.keys())
            or not set(arguments.keys()).issubset(
                required_arguments | optional_arguments
            )
        ):
            return {
                "success": False,
                "error": (
                    "Expected selected_assets, stress_ric, "
                    "start_date, end_date and optional "
                    "window, percentile, min_observations."
                )
            }

        # Validate selected assets.
        try:
            selected_rics = parse_selected_rics(
                arguments["selected_assets"]
            )
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Validate the stress indicator.
        stress_ric = arguments["stress_ric"]

        if (
            not isinstance(stress_ric, str)
            or stress_ric not in SUPPORTED_RICS
        ):
            return {
                "success": False,
                "error": "Unsupported stress indicator RIC."
            }

        if stress_ric not in selected_rics:
            return {
                "success": False,
                "error": (
                    "The stress indicator must also be included "
                    "in selected_assets."
                )
            }

        # Validate dates.
        try:
            start_date, end_date = validate_date_range(
                arguments["start_date"],
                arguments["end_date"]
            )
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Read optional parameters.
        window = arguments.get("window", 21)
        percentile = arguments.get("percentile", 0.90)
        min_observations = arguments.get("min_observations", 15)

        # Validate rolling window.
        if (
            isinstance(window, bool)
            or not isinstance(window, int)
            or window < 2
        ):
            return {
                "success": False,
                "error": "window must be an integer of at least 2."
            }

        # Validate stress percentile.
        if (
            isinstance(percentile, bool)
            or not isinstance(percentile, (int, float))
            or not 0 < percentile < 1
        ):
            return {
                "success": False,
                "error": "percentile must be between 0 and 1."
            }

        # Validate minimum observations.
        if (
            isinstance(min_observations, bool)
            or not isinstance(min_observations, int)
            or min_observations < 2
        ):
            return {
                "success": False,
                "error": (
                    "min_observations must be an integer "
                    "of at least 2."
                )
            }

        try:
            # 1. Retrieve historical prices.
            open_lseg_session()

            prices, failures = fetch_multiple_assets(
                selected_rics,
                start_date,
                end_date
            )

            if prices.shape[1] < 2:
                raise ValueError(
                    "At least two assets must have successfully "
                    "retrieved historical prices."
                )

            if stress_ric not in prices.columns:
                raise ValueError(
                    "Historical data for the stress indicator "
                    "could not be retrieved."
                )

            # 2. Calculate daily returns.
            returns = calculate_daily_returns(prices)

            # 3. Calculate rolling annualized volatility.
            rolling_volatility = calculate_rolling_volatility(
                returns,
                window=window
            )

            # 4. Classify stress periods using the selected indicator.
            stress_periods, stress_threshold = identify_stress_periods(
                rolling_volatility[stress_ric],
                percentile=percentile
            )

            # Exclude dates for which rolling volatility is unavailable.
            classified_stress = (
                stress_periods.dropna().astype(bool)
            )

            if classified_stress.empty:
                raise ValueError(
                    "No observations could be classified into "
                    "stress regimes."
                )

            classified_returns = returns.loc[
                classified_stress.index
            ]

            # 5. Calculate regime-specific statistics.
            regime_statistics = calculate_regime_statistics(
                classified_returns,
                classified_stress
            )

            # 6. Calculate conditional correlation matrices.
            conditional_correlations = (
                calculate_conditional_correlations(
                    classified_returns,
                    classified_stress,
                    min_observations=min_observations
                )
            )

            # Count observations in each regime.
            stress_count = int(classified_stress.sum())
            non_stress_count = int((~classified_stress).sum())

            # Convert results into JSON-serializable structures.
            return {
                "success": True,
                "tool": tool_name,

                "date_range": {
                    "start": start_date,
                    "end": end_date
                },

                "assets": [
                    {
                        "ric": ric,
                        "name": ASSET_MAPPING[ric]
                    }
                    for ric in prices.columns
                ],

                "stress_indicator": {
                    "ric": stress_ric,
                    "name": ASSET_MAPPING[stress_ric],
                    "window": window,
                    "percentile": percentile,
                    "annualized_volatility_threshold": float(
                        stress_threshold
                    )
                },

                "regime_observations": {
                    "stress": stress_count,
                    "non_stress": non_stress_count,
                    "total_classified": len(classified_stress)
                },

                "regime_statistics": regime_statistics,

                "min_observations": min_observations,

                "conditional_correlations": {
                    regime: {
                        "correlation_matrix": dataframe_to_dict(
                            results["correlation_matrix"]
                        ),
                        "observation_counts": dataframe_to_dict(
                            results["observation_counts"]
                        )
                    }
                    for regime, results
                    in conditional_correlations.items()
                },

                "failures": failures
            }

        except Exception as e:
            print(
                f"Stress regime analysis failed: "
                f"{type(e).__name__}: {e}"
            )

            return {
                "success": False,
                "error": (
                    "Unable to complete stress regime analysis."
                )
            }
