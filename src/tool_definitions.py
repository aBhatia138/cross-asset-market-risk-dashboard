
GET_ASSET_SNAPSHOT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_asset_snapshot",
        "description": (
            "Retrieve the latest available price and quantitative "
            "risk metrics for a supported financial instrument. "
            "Use this tool when the user asks for an asset's "
            "price, volatility, drawdown or daily return."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ric": {
                    "type": "string",
                    "description": (
                        "LSEG instrument identifier. "
                        "Use one of these exact identifiers: "
                        "XAU=, EUR=, JPY=, or .STOXX50E."
                    )
                }
            },
            "required": ["ric"],
            "additionalProperties": False
        }
    }
}


GET_DASHBOARD_SNAPSHOT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_dashboard_snapshot",
        "description": (
            "Retrieve the instrument, historical date range, "
            "price information and quantitative risk metrics "
            "for the dataset currently displayed on the user's "
            "dashboard. Use this tool whenever the user refers "
            "to the current instrument, displayed instrument, "
            "selected dashboard data or the displayed historical "
            "period. This tool requires no arguments."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    }
}

COMPARE_ASSETS_TOOL = {
    "type": "function",
    "function": {
        "name": "compare_assets",
        "description": (
            "Compare a quantitative financial metric across "
            "multiple supported financial instruments. "
            "Use this tool when the user asks to compare "
            "assets by volatility, drawdown, price, daily "
            "return or number of observations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "metric_name": {
                    "type": "string",
                    "enum": [
                        "Observations",
                        "Annualized Volatility",
                        "Maximum Drawdown",
                        "Latest Price",
                        "Latest Daily Return"
                    ],
                    "description": (
                        "The financial metric to compare. "
                    )
                },
                "selected_assets": {
                    "type": "string",
                    "items": {
                        "type": "string",
                        "enum": [
                            "XAU=",
                            "EUR=",
                            "JPY=",
                            ".STOXX50E"
                        ]
                    },
                    "description": (
                        "Comma-separated list of supported instrument RICs. "
                        "Example: EUR=,JPY=,XAU= "
                    ),
                    "minItems": 2,
                    "uniqueItems": True
                }
            },
            "required": [
                "metric_name",
                "selected_assets"
            ],
            "additionalProperties": False
        }
    }
}

RANK_ASSETS_TOOL = {
    "type": "function",
    "function": {
        "name": "rank_assets",
        "description": (
            "Rank multiple supported financial instruments "
            "according to a quantitative financial metric. "
            "Use this tool when the user asks which asset "
            "has the highest or lowest volatility, best daily "
            "return or smallest maximum drawdown. "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "metric_name": {
                    "type": "string",
                    "enum": [
                        "Annualized Volatility",
                        "Maximum Drawdown",
                        "Latest Daily Return"
                    ],
                    "description": (
                        "Metric used to rank the instruments."
                    )
                },
                "selected_assets": {
                    "type": "string",
                    "items": {
                        "type": "string",
                        "enum": [
                            "XAU=",
                            "EUR=",
                            "JPY=",
                            ".STOXX50E"
                        ]
                    },
                    "description": (
                        "Comma-separated list of supported instrument RICs. "
                        "Example: EUR=,JPY=,XAU="
                    ),
                    "minItems": 2,
                    "uniqueItems": True
                }
            },
            "required": [
                "metric_name",
                "selected_assets"
            ],
            "additionalProperties": False
        }
    }
}

GET_HISTORICAL_VOLATILITY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_historical_volatility",
        "description": (
            "Calculate historical rolling annualized volatility "
            "for one supported financial instrument over a specified "
            "date range. Use this tool when the user asks about "
            "historical volatility, changes in volatility over time, "
            "or rolling volatility. This is a historical analysis, "
            "not a volatility forecast. "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ric": {
                    "type": "string",
                    "enum": [
                        "XAU=",
                        "EUR=",
                        "JPY=",
                        ".STOXX50E"
                    ],
                    "description": "Supported LSEG instrument RIC."
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date in YYYY-MM-DD format."
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End date in YYYY-MM-DD format."
                },
                "window": {
                    "type": "integer",
                    "minimum": 2,
                    "default": 21,
                    "description": (
                        "Rolling window in trading observations. "
                        "Use 21 by default. "
                    )
                }
            },
            "required": [
                "ric",
                "start_date",
                "end_date"
            ],
            "additionalProperties": False
        }
    }
}

GET_CROSS_ASSET_CORRELATIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_cross_asset_correlations",
        "description": (
            "Calculate the Pearson correlation matrix and pairwise"
            "observation counts for multiple supported financial"
            "instruments over a specified historical date range."
            "Use this tool when the user asks about correlations,"
            "relationships or diversification across assets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "selected_assets": {
                    "type": "string",
                    "description": (
                        "Comma-separated list of supported instrument "
                        "RICs. Atleast two distinct instruments are "
                        "required. Example: XAU=,EUR=,.STOXX50E "
                    )
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date in YYYY-MM-DD format. "
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End date in YYYY-MM-DD format. "
                },
                "min_observations": {
                    "type": "integer",
                    "minimum": 2,
                    "default": 30,
                    "description": (
                        "Minimum number of pairwise observations "
                        "required to calculate a correlation. "
                        "Use 30 by default. "
                    )
                }
            },
            "required": [
                "selected_assets",
                "start_date",
                "end_date"
            ],
            "additionalProperties": False
        }
    }
}

GET_STRESS_REGIME_ANALYSIS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_stress_regime_analysis",
        "description": (
            "Perform historical stress-regime analysis across "
            "multiple supported financial instruments. Identify "
            "stress periods using the rolling volatility of a "
            "selected stress-indicator instrument, calculate "
            "asset-level return and volatility statistics in "
            "stress and non-stress regimes, and calculate "
            "conditional correlation matrices. Use this tool "
            "when the user asks how assets behave during market "
            "stress or wants to compare normal and stressed "
            "market conditions. This is retrospective analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "selected_assets": {
                    "type": "string",
                    "description": (
                        "Comma-separated list of supported instrument "
                        "RICs to include in the analysis. At least "
                        "two distinct instruments required. "
                    )
                },
                "stress_ric": {
                    "type": "string",
                    "enum": [
                        "XAU=",
                        "EUR=",
                        "JPY=",
                        ".STOXX50E"
                    ],
                    "description": (
                        "Instrument whose rolling volatility determines "
                        "the stress classification. "
                    )
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date in YYYY-MM-DD format. "
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End date in YYYY-MM-DD format. "
                },
                "window": {
                    "type": "integer",
                    "minimum": 2,
                    "default": 21,
                    "description": (
                        "Rolling volatility window in trading "
                        "observations. Use 21 by default. "
                    )
                },
                "percentile": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "exclusiveMaximum": 1,
                    "default": 0.90,
                    "description": (
                        "Volatility percentile used as the stress "
                        "threshold. Use 0.90 by default. "
                    )
                },
                "min_observations": {
                    "type": "integer",
                    "minimum": 2,
                    "default": 15,
                    "description": (
                        "Minimum pairwise observations required "
                        "for conditional correlations. Use 15 "
                        "by default. "
                    )
                }
            },
            "required": [
                "selected_assets",
                "stress_ric",
                "start_date",
                "end_date"
            ],
            "additionalProperties": False
        }
    }
}

TOOLS = [
    GET_ASSET_SNAPSHOT_TOOL,
    GET_DASHBOARD_SNAPSHOT_TOOL,
    COMPARE_ASSETS_TOOL,
    RANK_ASSETS_TOOL,
    GET_HISTORICAL_VOLATILITY_TOOL,
    GET_CROSS_ASSET_CORRELATIONS_TOOL,
    GET_STRESS_REGIME_ANALYSIS_TOOL
]

import json

#Validate that all tool definitions are JSON serializable
json.dumps(TOOLS)

print("Tool definitions passed JSON serialization validations")