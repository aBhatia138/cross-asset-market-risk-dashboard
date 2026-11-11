from .data_loader import fetch_live_feed
from src.lseg_session import open_lseg_session
from datetime import date, timedelta
from .risk_metrics import calculate_metrics
# import refinitiv.data as rd

def get_asset_snapshot(ric):

    try:
        open_lseg_session()

        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        prices = fetch_live_feed(
            ric,
            start_date,
            end_date
        )

        if prices is None or prices.empty:
            raise ValueError(
                f"No historical data available for {ric}"
            )

        if len(prices) < 2:
            raise ValueError(
                "Insufficient price observations"
            )
        
        results = calculate_metrics(prices)

        if not results or not results.get("metrics"):
            raise ValueError(
                "Risk metrics could not be calculated"
            )

        return results
    
    except Exception as e:
        raise RuntimeError(
            f"Unable to analyse {ric}: {e}"
        ) from e


def compare_assets(metric_name,selected_assets):
    #Retrieve a selected metric for each asset
    #Returns a dictionary mapping asset names to raw metric values
    #If retrieval or calculation fails for an asset, its value is None

    valid_metrics = {
        "Observations",
        "Annualized Volatility",
        "Maximum Drawdown",
        "Latest Price",
        "Latest Daily Return"
    }

    if metric_name not in valid_metrics:
        raise ValueError(
            f"Unsupported metric: {metric_name}"
            f"Choose from: {', '.join(valid_metrics)}"
        )

    comparison = {}

    for asset_name, asset_details in selected_assets.items():
        try:
            ric = asset_details["ric"]

            results = get_asset_snapshot(ric)

            if not results or "metrics" not in results:
                raise ValueError(
                    f"Risk Metrics are unavailable for {asset_name}"
                )

            metrics = results["metrics"]

            if metric_name not in metrics:
                raise ValueError(
                    f"{metric_name} unavailable for {asset_name}"
                )

            #Preserve the original value; do not multiply by 100
            comparison[asset_name] = metrics[metric_name]

        except Exception as e:
            comparison[asset_name] = None
            print(f"Error retrieving {asset_name}: {e}")

    return comparison

def rank_assets(comparison, metric_name):
    #Rank assets according to selected metric
    #Lower volatility is ranked first 
    #Less negative drawdown and higher daily returns are ranked first

    ranking_directions = {
        "Annualized Volatility": False,
        "Maximum Drawdown": True,
        "Latest Daily Return": True
    }

    if metric_name not in ranking_directions:
        raise ValueError(
            f"Ranking is not supposed to be for {metric_name}. "
            f"Supported metrics: {', '.join(ranking_directions)}"
        )

    valid_results = {
        asset: value
        for asset, value in comparison.items()
        if value is not None
    }

    ranked_assets = sorted(
        valid_results.items(),
        key=lambda item: item[1],
        reverse=ranking_directions[metric_name]
    )

    return ranked_assets

def get_latest_asset_price(ric):

    open_lseg_session()
    # rd.open_session()

    end_date = date.today()
    start_date = end_date - timedelta(days=14)

    prices = fetch_live_feed(
        ric,
        start_date,
        end_date
    )

    latest_price = prices.iloc[-1]
    latest_date = prices.index[-1]

    return latest_price, latest_date


def get_data_response(user_message):

    message = user_message.lower().strip()

    # Step 1: Identify whether the user is asking about a price
    price_keywords = [
        "latest price",
        "current price",
        "closing price",
        "price of",
        "price for",
        "latest",
        "current"
    ]

    if not any(keyword in message for keyword in price_keywords):
        return None

    # Step 2: Create an instrument dictionary
    assets = {
        "STOXX50E": {
            "ric": ".STOXX50E",
            "keywords": ["stoxx50e", "stoxx 50e", "stoxx 50", "euro stoxx"],
            "name": "STOXX 50",
            "unit": "index points"
        },

        "Gold": {
            "ric": "XAU=",
            "keywords": ["gold", "xau"],
            "name": "Gold",
            "unit": "quoted price"
        },

        "JPY/USD": {
            "ric": "JPY=",
            "keywords": ["jpy", "jpy/usd", "japanese yen", "yen"],
            "name": "Japanese yen",
            "unit": "quoted exchange rate"
        },

        "EUR/USD": {
            "ric": "EUR=",
            "keywords": ["eur/usd", "eur", "euro"],
            "name": "Euro",
            "unit": "quoted exchange rate"
        }
    }

    # Step 3: Identify the requested instrument
    selected_asset = None

    for asset in assets.values():

        if any(keyword in message for keyword in asset["keywords"]):
            selected_asset = asset
            break

    if selected_asset is None:
        return None

    # Step 4: Retrieve the latest price
    try:
        price, price_date = get_latest_asset_price(
            selected_asset["ric"]
        )

        return (
            f"The latest available {selected_asset['name']} "
            f"closing price is **{price:,.4f} "
            f"{selected_asset['unit']}**, "
            f"recorded on **{price_date:%d %B %Y}**."
        )

    except Exception as e:

        return (
            f"I couldn't retrieve the latest "
            f"{selected_asset['name']} price from "
            f"LSEG Workspace. Error: {e}"
        )


def get_risk_response(user_message):
    message = user_message.lower().strip()

    #Identify the requested metric
    metric_keywords = {
        "Annualized Volatility": [
            "volatility",
            "volatile",
            "annualized risk"
        ],

        "Maximum Drawdown": [
            "maximum drawdown",
            "max drawdown",
            "drawdown"
        ],

        "Latest Daily Return": [
            "daily return",
            "latest return",
            "daily performance"
        ],

        "Observations": [
            "observations",
            "number of observations",
            "data points"
        ]
    }

    selected_metric = None

    for metric, keywords in metric_keywords.items():
        if any(keyword in message for keyword in keywords):
            selected_metric = metric
            break

    if selected_metric is None:
        return None

    #Identify the requested asset:
    assets = {
        "STOXX50E": {
            "ric":".STOXX50E",
            "keywords":["stoxx50e", "stoxx 50e", "stoxx 50", "euro stoxx"],
            "name":"STOXX 50"
        },

        "Gold": {
            "ric":"XAU=",
            "keywords":["gold","xau"],
            "name":"Gold"
        },

        "JPY/USD": {
            "ric":"JPY=",
            "keywords":["jpy/usd", "jpy", "japanese yen", "yen"],
            "name":"JPY/USD"
        },

        "EUR/USD": {
            "ric":"EUR=",
            "keywords":["eur/usd", "eur", "euro"],
            "name":"EUR/USD"
        }
          
    }

    selected_asset = None

    for asset in assets.values():
        if any(keyword in message for keyword in asset["keywords"]):
            selected_asset = asset
            break

    if selected_asset is None:
        return None

    #Retrieve the requested metric
    try:
        result = get_asset_snapshot(selected_asset["ric"])
        value = result["metrics"][selected_metric]
        if selected_metric in ["Annualized Volatility",
            "Maximum Drawdown",
            "Latest Daily Return"]:
            formatted_value = f"{value * 100:.2f}%"
        else:
            formatted_value = f"{value:,}"

        return (
            f"The {selected_metric.lower()} of "
            f"**{selected_asset['name']}** is "
            f"**{formatted_value}**."
        )

    except Exception as e:
        return (
            f"I couldn't calculate {selected_metric.lower()} "
            f"for {selected_asset['name']}. "
            f"Error: {e}"
        )

def format_comparison_value(metric_name, value):

    if value is None:
        return "Unavailable"

    percentage_metrics = {
        "Annualized Volatility",
        "Maximum Drawdown",
        "Latest Daily Return"
    }

    if metric_name in percentage_metrics:
        return f"{value * 100:.2f}%"

    if metric_name == "Latest Price":
        return f"{value:.4f}"

    if metric_name == "Observations":
        return f"{int(value):,} observations"

    return str(value)


def get_comparison_response(user_message):

    message = user_message.lower().strip()

    comparison_keywords = [
        "compare", "rank", "which asset", "most volatile",
        "least volatile", "more volatile", "less volatile"
    ]

    if not any(word in message for word in comparison_keywords):
        return None

    assets = {
        "STOXX 50": {
            "ric": ".STOXX50E",
            "keywords": ["stoxx 50", "stoxx50e", "euro stoxx"]
        },
        "Gold": {
            "ric": "XAU=",
            "keywords": ["gold", "xau"]
        },
        "EUR/USD": {
            "ric": "EUR=",
            "keywords": ["eur/usd", "euro", "eur"]
        },
        "JPY/USD": {
            "ric": "JPY=",
            "keywords": ["jpy/usd", "yen", "jpy"]
        }
    }

    metric_keywords = {
        "Annualized Volatility": ["volatility", "volatile"],
        "Maximum Drawdown": ["maximum drawdown", "drawdown"],
        "Observations": ["observations", "number of", "length"],
        "Latest Price": ["latest price", "recent price", "price"],
        "Latest Daily Return": [
            "latest daily returns", "latest returns", "returns", "return"
        ]
    }

    selected_metric = None

    for metric, keywords in metric_keywords.items():
        if any(keyword in message for keyword in keywords):
            selected_metric = metric
            break

    if selected_metric is None:
        return None

    rank_all = any(
        phrase in message
        for phrase in [
            "rank the assets", "rank", "all four", "all assets",
            "every asset", "most volatile", "least volatile"
        ]
    )

    selected_assets = {}

    for asset_name, details in assets.items():
        if any(keyword in message for keyword in details["keywords"]):
            selected_assets[asset_name] = details

    rankable_metrics = {
        "Annualized Volatility",
        "Maximum Drawdown",
        "Latest Daily Return"
    }

    try:

        # CASE 1: Rank all supported assets
        if rank_all:

            comparison = compare_assets(selected_metric, assets)

            if selected_metric not in rankable_metrics:

                available = {
                    asset: value
                    for asset, value in comparison.items()
                    if value is not None
                }

                if not available:
                    return (
                        f"I couldn't retrieve {selected_metric} "
                        "data for the supported assets."
                    )

                response = (
                    f"Here are the {selected_metric.lower()} values. "
                    "They are not ranked because their numerical "
                    "magnitudes do not provide a meaningful "
                    "risk or return ranking:\n\n"
                )

                for asset, value in comparison.items():
                    formatted_value = _format_comparison_value(
                        selected_metric, value
                    )

                    response += f"- **{asset}**: {formatted_value}\n"

                return response

            ranked = rank_assets(comparison, selected_metric)

            if not ranked:
                return (
                    f"I couldn't retrieve {selected_metric} "
                    "data for the supported assets."
                )

            if selected_metric == "Annualized Volatility":
                direction = "lowest volatility first"
                winner_label = "Lowest-volatility asset"

            elif selected_metric == "Maximum Drawdown":
                direction = "least severe drawdown first"
                winner_label = "Least severe maximum drawdown"

            else:
                direction = "highest return first"
                winner_label = "Highest daily return"

            response = (
                f"Here is the ranking by {selected_metric} "
                f"({direction}):\n\n"
            )

            for rank, (asset, value) in enumerate(ranked, start=1):

                formatted_value = _format_comparison_value(
                    selected_metric, value
                )

                response += (
                    f"{rank}. **{asset}**: {formatted_value}\n\n"
                )

            response += (
                f"{winner_label}: **{ranked[0][0]}**."
            )

            return response

        # CASE 2: Compare exactly two selected assets
        if len(selected_assets) == 2:

            comparison = compare_assets(
                selected_metric,
                selected_assets
            )

            if selected_metric not in rankable_metrics:

                response = (
                    f"Here are the {selected_metric.lower()} "
                    "values. These are not ranked:\n\n"
                )

                for asset, value in comparison.items():

                    formatted_value = _format_comparison_value(
                        selected_metric, value
                    )

                    response += f"- **{asset}**: {formatted_value}\n"

                return response

            ranked = rank_assets(comparison, selected_metric)

            if len(ranked) != 2:
                return "I couldn't retrieve data for both assets."

            first_asset, first_value = ranked[0]
            second_asset, second_value = ranked[1]

            first_formatted = _format_comparison_value(
                selected_metric, first_value
            )

            second_formatted = _format_comparison_value(
                selected_metric, second_value
            )

            if first_value == second_value:

                return (
                    f"Both assets have the same "
                    f"{selected_metric.lower()}.\n\n"
                    f"- {first_asset}: **{first_formatted}**\n"
                    f"- {second_asset}: **{second_formatted}**"
                )

            if selected_metric == "Annualized Volatility":
                description = "lower annualized volatility"

            elif selected_metric == "Maximum Drawdown":
                description = "a less severe maximum drawdown"

            else:
                description = "a higher latest daily return"

            difference = abs(first_value - second_value) * 100

            return (
                f"**{first_asset}** has {description} "
                f"than **{second_asset}**.\n\n"
                f"- {first_asset}: **{first_formatted}**\n"
                f"- {second_asset}: **{second_formatted}**\n\n"
                f"Difference: **{difference:.2f} "
                "percentage points**."
            )

        return (
            "Please specify two assets to compare, "
            "or ask me to rank all four supported assets."
        )

    except Exception as e:
        return f"I encountered an error while comparing assets: {e}"