# System Architecture

## 1. Overview

The Cross-Asset Market Risk Dashboard is a Streamlit-based application that combines historical market data retrieval, quantitative risk analytics, and an LLM-powered financial assistant.

The application has two main components:

1. **Market Risk Dashboard:** Retrieves historical market data through the LSEG Data API and presents price information, returns, volatility, drawdowns, and other risk metrics.
2. **MarketMate:** An LLM-powered assistant that uses Groq tool calling to answer questions about supported financial instruments and execute predefined quantitative analysis functions.

The application follows a modular architecture in which data retrieval, quantitative calculations, tool execution, LLM orchestration, and user-interface rendering are handled by separate modules.

## 2. High-Level Architecture

The application can be divided into five logical layers:

| Layer | Responsibility | Main modules |
|---|---|---|
| User Interface | Displays the dashboard and chatbot | `app.py`, `dashboard_ui.py`, `chatbot_ui.py` |
| Data Access | Retrieves and prepares market data | `lseg_session.py`, `data_loader.py`, `historical_data.py` |
| Quantitative Analytics | Calculates financial metrics and historical statistics | `risk_metrics.py`, `historical_analysis.py` |
| LLM Orchestration | Manages Groq requests and tool-calling interactions | `groq_client.py`, `tool_definitions.py` |
| Tool Execution | Validates and executes predefined analytical functions | `tool_registry.py`, `marketmate.py` |

These layers communicate through function calls and structured Python data objects.

## 3. Dashboard Execution Flow

The main application entry point is `app.py`.

The dashboard follows this general execution sequence:

1. Streamlit initializes the application and renders the sidebar.
2. The user selects a financial instrument (RIC) and a historical date range.
3. When the user requests data, the application opens or reuses an LSEG session through `lseg_session.py`.
4. `data_loader.py` retrieves historical daily market data using the LSEG Data API.
5. The retrieved data is processed and passed to `risk_metrics.py`.
6. Quantitative metrics and visualizations are rendered through the dashboard interface.
7. A dashboard context containing relevant information is constructed and passed to MarketMate.

The dashboard context allows MarketMate to access information about the currently selected instrument, date range, observation period, and calculated metrics.

## 4. MarketMate Architecture

MarketMate combines an LLM with a predefined collection of Python analytical tools.

Rather than allowing the LLM to calculate financial metrics independently or execute arbitrary Python code, the application uses tool calling to delegate analytical operations to deterministic functions.

### 4.1 Request Lifecycle

A typical MarketMate interaction follows this sequence:

1. The user submits a natural-language question through `chatbot_ui.py`.
2. The chatbot interface passes the question and relevant dashboard context to `groq_client.py`.
3. The Groq client sends the request to the configured language model.
4. The model determines whether one or more registered tools are required.
5. Tool definitions from `tool_definitions.py` describe the available functions and their expected arguments.
6. `tool_registry.py` validates and routes tool requests to the corresponding Python implementation.
7. The selected function retrieves data or performs the requested quantitative analysis.
8. The tool result is returned to the Groq client.
9. The model uses the result to formulate a natural-language response.
10. The chatbot interface displays the response and, where applicable, associated visualizations.

The orchestration layer supports multiple tool-calling rounds, subject to the configured maximum.

### 4.2 Tool Registry

The tool registry acts as the controlled execution layer between the LLM and the application's Python functions.

The `execute_tool()` function validates incoming tool names and arguments before routing requests to the corresponding analytical implementations.

MarketMate currently exposes seven tools:

- `get_asset_snapshot`: Retrieves the latest available price and risk metrics for a supported instrument.
- `get_dashboard_snapshot`: Retrieves information and calculated metrics from the active dashboard context.
- `compare_assets`: Compares multiple instruments using a supported quantitative metric.
- `rank_assets`: Ranks selected instruments according to a supported metric.
- `get_historical_volatility`: Calculates rolling annualized historical volatility for a selected instrument.
- `get_cross_asset_correlations`: Calculates pairwise Pearson correlations and corresponding observation counts for selected instruments.
- `get_stress_regime_analysis`: Identifies historical stress periods using a selected instrument's rolling volatility and calculates regime-specific statistics and conditional correlations.

The registry validates instrument identifiers, argument structures, date ranges, and analytical parameters before executing a tool.

The implementation uses an explicit allowlist of supported operations, preventing the LLM from executing arbitrary Python code through the tool interface.

Historical data retrieval failures are captured and returned where possible, allowing analyses to proceed with successfully retrieved instruments when the minimum requirements are satisfied.

### 4.3 Supported Instruments

MarketMate currently supports the following instruments:

| Instrument | LSEG RIC |
|---|---|
| Gold | `XAU=` |
| EUR/USD | `EUR=` |
| JPY/USD | `JPY=` |
| EURO STOXX 50 | `.STOXX50E` |

The dashboard itself accepts a user-selected RIC, subject to the user's LSEG Workspace permissions and data entitlements.

## 5. Historical Cross-Asset Analysis

The historical analysis modules provide the quantitative foundation for MarketMate's multi-asset analytical capabilities.

The general processing pipeline is:

1. Retrieve historical prices for the selected instruments.
2. Align the price series by observation date.
3. Calculate daily returns.
4. Calculate rolling volatility and correlation statistics.
5. Identify periods of elevated market volatility.
6. Compare statistical behaviour across stress and non-stress regimes.
7. Return structured analytical results to the tool registry.

### 5.1 Historical Data Preparation

`historical_data.py` coordinates the retrieval and alignment of multiple price series.

The resulting dataset is structured as a pandas DataFrame, with observation dates as the index and individual instruments represented by columns.

Missing observations are retained during alignment rather than automatically forward-filled.

### 5.2 Quantitative Calculations

`historical_analysis.py` contains the principal historical analytical functions:

| Function | Purpose |
|---|---|
| `calculate_daily_returns()` | Calculates daily percentage returns from aligned prices. |
| `calculate_rolling_volatility()` | Calculates rolling annualized volatility. |
| `calculate_corr_matrix()` | Calculates pairwise asset correlations. |
| `identify_stress_periods()` | Identifies periods of elevated rolling volatility. |
| `calculate_regime_statistics()` | Compares return statistics across market regimes. |
| `calculate_conditional_correlations()` | Calculates correlations separately during stress and non-stress periods. |

### 5.3 Stress-Regime Analysis

Stress periods are identified using a percentile threshold applied to rolling volatility.

The analysis then separates observations into stress and non-stress regimes and calculates relevant statistics for each regime.

Conditional correlations allow users to examine whether relationships between instruments differ during periods of elevated volatility.

These results are descriptive historical statistics. They should not be interpreted as forecasts or as evidence of causal relationships.

## 6. Quantitative Risk Metrics

`risk_metrics.py` provides the calculations used by the main dashboard.

The principal metrics include:

- **Annualized Volatility:** Standard deviation of daily returns multiplied by the square root of 252.
- **Maximum Drawdown:** Largest percentage decline from a previous running portfolio or asset value peak.
- **Latest Price:** Most recent available price in the retrieved dataset.
- **Latest Daily Return:** Most recent daily percentage return.
- **Observations:** Number of available observations in the dataset.

These metrics provide a compact overview of the selected instrument's historical behaviour.

## 7. Visualization Architecture

The application separates general dashboard visualizations from MarketMate-specific analytical visualizations.

- `dashboard_ui.py` contains reusable dashboard interface and chart-styling components.
- `marketmate_visualizations.py` contains visualizations associated with MarketMate's analytical responses.
- Plotly is used to generate interactive charts and visual representations of quantitative results.
- Streamlit renders these components within the application.

Depending on the analytical request, MarketMate can present results through numerical summaries, comparisons, correlation heatmaps, and stress-analysis visualizations.

### 7.1 Stress Regime Mehodology 

For stress-regime analysis, the user selects a stress-indicator instrument through the `stress_ric` parameter. The application uses that instrument's rolling annualized volatility to calculate the percentile threshold and classify stress observations.

The resulting stress classification is then applied to the return series of all successfully retrieved selected instruments. This allows the application to compare the behaviour of multiple assets under regimes defined by the volatility of a single reference instrument.

## 8. External Services and Configuration

### LSEG Workspace

The application uses the LSEG Data API to retrieve historical financial market data.

An authenticated LSEG Workspace environment and appropriate data entitlements are required. Access to individual instruments may vary depending on the user's account permissions.

### Groq API

MarketMate uses the Groq API to access the configured language model.

The model is responsible for interpreting natural-language requests, selecting appropriate tools, and generating explanations based on the returned analytical results.

The API key is loaded from an environment variable using `python-dotenv`.

The application expects the following configuration:

```text
GROQ_API_KEY=your_groq_api_key_here
```

API credentials should never be committed to version control.

## 9. Error Handling and Testing

The project includes automated unit tests covering quantitative calculations, historical data processing, tool execution, and MarketMate functionality.

The test suite uses Python's `unittest` framework, with mocking employed where appropriate to isolate application logic from external services.

The tests are intended to verify:

- Input validation and error handling.
- Correctness of quantitative calculations.
- Handling of missing or invalid data.
- Correct routing and execution of registered tools.
- Behaviour of MarketMate's analytical functions.

External-service integration and live-data tests may have different execution requirements because they depend on valid credentials, network connectivity, and LSEG Workspace access.

## 10. Design Considerations and Limitations

The architecture incorporates several design considerations:

- **Modularity:** Data retrieval, calculations, LLM orchestration, and presentation are separated into individual modules.
- **Controlled execution:** The LLM can invoke only predefined analytical tools exposed through the registry.
- **Reproducibility:** Quantitative calculations are performed by Python functions rather than relying on the LLM to generate numerical results.
- **Data availability:** Historical analysis depends on the availability and quality of retrieved market observations.
- **LLM limitations:** Natural-language responses may still contain interpretation errors. Numerical results should be checked against the underlying analytical outputs.
- **Historical interpretation:** Stress-regime classifications and conditional correlations describe the selected historical sample and are not predictive guarantees.
- **External dependencies:** The application requires access to the Groq API and an appropriately authenticated LSEG Workspace environment.

The application is intended as an educational and analytical market-risk project. It is not an investment recommendation system or a substitute for institutional risk-management infrastructure.

### Minimum Observation Requirements

The application uses different default minimum-observation requirements depending on the analysis:

- General cross-asset correlation analysis: 30 paired observations.
- Stress-regime conditional correlation analysis: 15 paired observations per instrument pair and regime.

Both requirements can be modified through the corresponding tool arguments.

The observation-count matrices are returned alongside correlation matrices so that users can assess the sample size underlying individual estimates.

The lower default requirement for stress-regime analysis accommodates the smaller number of observations that may be available within individual regimes. However, estimates based on fewer observations should be interpreted with additional caution.