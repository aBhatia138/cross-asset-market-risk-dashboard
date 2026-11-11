
import os
import time
import json
import traceback

from dotenv import load_dotenv
from groq import Groq

from .tool_definitions import TOOLS
from .tool_registry import execute_tool


load_dotenv()

MODEL_NAME = "openai/gpt-oss-20b"

MAX_TOOL_ROUNDS = 3


SYSTEM_INSTRUCTIONS = """
You are MarketMate, a helpful financial market assistant.

Answer clearly, accurately and concisely. Use approved tools
whenever quantitative market data is required.

TOOL SELECTION RULES:

1. Use get_dashboard_snapshot when the user refers to:
   - The current dashboard instrument.
   - The currently selected instrument.
   - The asset displayed on the dashboard.
   - The dashboard's displayed metrics or historical period.
   - Phrases such as "this asset", "the current chart",
     or "the data shown above", when referring to the dashboard.

2. Use get_asset_snapshot when the user explicitly asks about
   one supported instrument independently of the dashboard.

3. Use compare_assets when the user asks to:
   - Compare two or more supported instruments.
   - Compare their volatility, drawdown, latest price,
     latest daily return or number of observations.
   - Understand how a particular metric differs across assets.

4. Use rank_assets when the user asks to:
   - Rank multiple supported instruments.
   - Identify the highest or lowest asset for a metric.
   - Find the most or least volatile asset.
   - Identify the asset with the best or worst drawdown.
   - Identify the asset with the highest or lowest daily return.

5. Supported instruments for independent asset,
   comparison and ranking tools:
   - Gold: XAU=
   - EUR/USD: EUR=
   - JPY/USD: JPY=
   - Euro STOXX 50: .STOXX50E

6. When the user says "all supported assets" or "all assets"
   in the context of a comparison or ranking, use all four
   supported instruments.

7. Do not use compare_assets or rank_assets for a request
   involving only one instrument.

8. Do not use get_dashboard_snapshot as a substitute for
   comparing or ranking multiple instruments.

HISTORICAL ANALYSIS TOOL SELECTION RULES:

A. Use get_historical_volatility when the user asks for:
   - Historical or rolling volatility of a supported instrument.
   - A time series of rolling annualized volatility.
   - Volatility calculated over a specified historical period.

B. Use get_cross_asset_correlations when the user asks for:
   - Correlations between two or more supported instruments.
   - A historical cross-asset correlation matrix.
   - Pairwise correlation values and observation counts.

C. Use get_stress_regime_analysis when the user asks for:
   - Historical stress and non-stress regime analysis.
   - How asset returns or volatility behave during market stress.
   - Differences in cross-asset correlations during stress
     and non-stress periods.

D. Historical analysis parameter rules:
   - Use only the four supported instruments.
   - Never invent dates or historical observations.
   - Use explicitly requested date ranges when provided.
   - When the user refers to the current dashboard instrument,
     "this asset", or the displayed historical period, use
     the dashboard's actual start_date and end_date.
   - The dashboard date range takes precedence over asking
     the user for dates when the question refers to dashboard data.
   - If neither an explicit date range nor applicable dashboard
     dates are available, ask the user to provide a date range.
   - Use a rolling window of 21 observations unless
     the user specifies another valid window.
   - Use a 90th percentile stress threshold unless
     the user specifies another valid percentile.
   - Use 15 as the default minimum pairwise observation count
     for conditional correlations.

E. Stress-regime analysis:
   - The stress_ric must be one of the selected assets.
   - If the user explicitly requests equity-market stress,
     use Euro STOXX 50 (.STOXX50E) as the stress indicator
     and include it in selected_assets.
   - If the user refers to the current dashboard instrument
     without specifying another stress indicator, use the
     current dashboard instrument as the stress indicator.
   - Include both the instrument being analysed and the
     instrument used as the stress indicator in selected_assets.
   - Do not assume that every asset behaves as a safe haven
     during stress.
   - Explain that percentile-based stress classification
     is retrospective historical analysis, not a forecast
     or real-time predictive signal.

F. Distinguish the three historical-analysis tools from
   get_asset_snapshot and get_dashboard_snapshot.
   Use the historical-analysis tools when the user requests
   rolling volatility, correlation analysis or regime analysis.
   Use snapshot tools for the existing snapshot metrics.

9. For general questions unrelated to specific market data,
   answer normally without calling a tool.

METRIC AND RANKING RULES:

10. compare_assets supports:
    - Observations
    - Annualized Volatility
    - Maximum Drawdown
    - Latest Price
    - Latest Daily Return

11. rank_assets supports only:
    - Annualized Volatility
    - Maximum Drawdown
    - Latest Daily Return

12. Interpret ranking directions correctly:
    - Annualized Volatility: lower is better.
    - Maximum Drawdown: higher (less negative) is better.
    - Latest Daily Return: higher is better.

13. Do not rank Latest Price or Observations.
    If the user requests this, explain that these metrics
    are not supported for ranking.

TOOL CALL FORMATTING RULES:

- When invoking a tool, generate arguments that strictly conform
  to the tool's JSON schema.
- Tool arguments must be valid JSON objects.
- Use double quotes around JSON keys and string values.
- Do not add extra quotation marks, trailing characters,
  comments or explanations to tool arguments.
- Ensure every array and object is correctly closed.
- Never modify the arguments after generating valid JSON.

FINANCIAL DATA RULES:

14. Never invent financial prices, observations or risk metrics.

15. Base quantitative financial answers on data returned
    by the approved tools.

16. If a tool returns an error, explain the issue clearly.
    Do not fabricate a result or silently substitute another asset.

17. If a comparison contains null values, explain that data
    was unavailable for those instruments. Do not treat null
    as zero.

18. If a ranking excludes instruments with unavailable values,
    make clear that the ranking only includes assets for which
    a valid value was returned.

19. Annualized Volatility, Maximum Drawdown and Latest Daily
    Return are decimals. Convert them into percentages when
    explaining them.

20. Observations represents the number of price observations
    used in the calculation.

21. Latest Price is a price value, not a percentage.
    Do not convert it into a percentage.

22. Clearly distinguish historical measurements from
    forecasts or predictions. Do not present historical
    performance as a forecast.

23. When discussing a comparison or ranking, identify the
    metric and the instruments included.

24. If get_dashboard_snapshot reports that dashboard data
    is unavailable, explain that no dashboard data has
    currently been loaded. Do not substitute another asset.

25. Always provide RIC identifiers exactly as listed,
    without leading or trailing whitespaces.
"""


def generate_response(
    prompt: str,
    conversation_history: list[dict] | None = None,
    dashboard_context: dict | None = None,
    include_tool_results: bool = False
) -> str | dict:

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY was not found in .env file")

    client = Groq(
        api_key=api_key,
        timeout=30.0,
        max_retries=0
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTIONS
        }
    ]

    if dashboard_context:

        context_for_llm = {
            key: dashboard_context.get(key)
            for key in [
                "ric",
                "start_date",
                "end_date",
                "first_observation",
                "last_observation",
                "metrics"
            ]
            if dashboard_context.get(key) is not None
        }

        messages.append({
            "role": "system",
            "content": (
                "CURRENT DASHBOARD CONTEXT:\n"
                + json.dumps(context_for_llm, default=str)
                + "\n\n"
                "IMPORTANT DASHBOARD CONTEXT RULES:\n"
                "- This information represents the currently "
                "displayed dashboard instrument and date range.\n"
                "- When the user refers to 'this asset', 'the "
                "current asset', or the displayed dashboard period, "
                "use this context.\n"
                "- For historical analysis, use the dashboard "
                "start_date and end_date when the user does not "
                "specify another date range.\n"
                "- Never generate empty date strings.\n"
                "- If the required dashboard dates are unavailable, "
                "ask the user for a date range instead of inventing one.\n"
            )
        })

    # Restore previous conversation messages.
    if conversation_history:
        for message in conversation_history:

            role = message.get("role")
            content = message.get("content")

            if (
                role in {"user", "assistant"}
                and isinstance(content, str)
                and content.strip()
            ):
                messages.append({
                    "role": role,
                    "content": content
                })

    messages.append({
        "role": "user",
        "content": prompt.strip()
    })

    start = time.perf_counter()

    try:

        tool_rounds = 0

        tool_results = []

        while True:

            print("\n========== GROQ REQUEST DIAGNOSTICS ==========")


            print("========== END DIAGNOSTICS ==========\n")
            try:

                # STEP 1: Ask Groq to respond or request a tool.
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_completion_tokens=8000
                )

                response_message = completion.choices[0].message

            except Exception as e:

                error_message = str(e).lower()

                #Retry only when Groq reports malformed tool-call JSON
                malformed_tool_call = (
                    getattr(e,"status_code",None) == 400
                    and "tool" in error_message
                    and "arguments" in error_message
                    and "json" in error_message
                )

                if (malformed_tool_call):
                    print(
                        "Groq generated malformed tool arguments. "
                        "Retrying the request once... "
                    )

                    retry_messages = messages.copy()

                    retry_messages.insert(
                        1,
                        {
                            "role": "system",
                            "content": (
                                "Your previous tool-call generation was invalid. "
                                "If you call a tool, ensure its arguments are "
                                "strictly valid JSON and conform to the tool schema. "
                                "Do not include extra quotation marks or characters."
                            )
                        }
                    )

                    completion = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=retry_messages,
                        tools=TOOLS,
                        tool_choice="auto",
                        max_completion_tokens=1000
                    )

                    response_message = completion.choices[0].message

                else:
                    raise

            if completion.usage:
                print("Token usage:", completion.usage)

            # STEP 2: Check whether Groq requested a tool.
            tool_calls = response_message.tool_calls

            if not tool_calls:

                answer = response_message.content

                if not answer:
                    raise RuntimeError(
                        "Groq returned an empty response."
                    )

                elapsed = time.perf_counter() - start
                print(f"Groq response time: {elapsed:.2f} seconds")

                if include_tool_results:
                    return {
                        "answer": answer,
                        "tool_results": tool_results
                    }

                return answer

            # Prevent unlimited tool execution.
            if tool_rounds >= MAX_TOOL_ROUNDS:
                raise RuntimeError(
                    "Maximum number of tool-call rounds exceeded."
                )

            # Preserve Groq's assistant message, including
            # its tool-call information, in the conversation.
            messages.append(
                response_message.model_dump(exclude_none=True)
            )

            # STEP 3: Execute each requested tool.
            for tool_call in tool_calls:

                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments

                print(f"Groq requested tool: {tool_name}")
                print(f"Tool arguments: {raw_arguments}")

                try:
                    arguments = json.loads(raw_arguments)

                    if not isinstance(arguments, dict):
                        raise ValueError(
                            "Tool arguments must be a JSON object."
                        )

                    tool_result = execute_tool(
                        tool_name,
                        arguments,
                        dashboard_context=dashboard_context
                    )

                    print(
                        f"TOOL RESULT TYPE: {type(tool_result)}"
                    )

                    print(
                        f"TOOL RESULT: {tool_result}"
                    )

                except (json.JSONDecodeError, ValueError) as exc:

                    tool_result = {
                        "success": False,
                        "error": str(exc)
                    }

                if include_tool_results:
                    tool_results.append(
                        tool_result
                    )

                #Create a separate, compact result for the LLMs
                llm_tool_result = tool_result

                if (
                    tool_name == "get_historical_volatility"
                    and isinstance(tool_result, dict)
                ):
                    llm_tool_result = llm_tool_result.copy()
                    llm_tool_result.pop("rolling_volatility", None)

                # STEP 4: Return the tool result to Groq.
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(
                        llm_tool_result,
                        default=str
                    )
                })

            tool_rounds += 1

            # The loop now sends the tool result back to Groq.
            # Groq can generate an answer or request another tool.

    except Exception as exc:

        elapsed = time.perf_counter() - start

        print(
            f"Groq request failed after {elapsed:.2f} seconds"
        )

        traceback.print_exc()

        raise
