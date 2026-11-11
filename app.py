import streamlit as st
import plotly.express as px
import pandas as pd
from src.lseg_session import open_lseg_session
import traceback

from src.chatbot_ui import render_chatbot
from src.data_loader import fetch_live_feed
from src.risk_metrics import calculate_metrics
from src.dashboard_ui import (
    ACCENT,
    MUTED,
    NEGATIVE,
    POSITIVE,
    PURPLE,
    apply_theme,
    format_percentage,
    render_header,
    render_loading_indicator,
    style_chart,
)


st.set_page_config(
    page_title="Cross-Asset Market Metrics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

def render_sidebar():
    """Render controls and return the user's requested instrument window."""
    with st.sidebar:
        st.markdown("## MARKET TERMINAL")
        st.caption("LSEG Workspace · Historical Analytics")
        st.divider()

        st.markdown("### Instrument")
        ric = st.text_input(
            "Instrument RIC",
            value=".SPX",
            help="Examples: .SPX, .STOXX50E, EUR=, XAU=",
        ).strip()

        st.markdown("### Historical Window")
        start_date = st.date_input(
            "Start Date",
            value=pd.Timestamp("2026-10-01").date(),
        )
        end_date = st.date_input(
            "End Date",
            value=pd.Timestamp("2026-10-23").date(),
        )

        st.divider()
        fetch_clicked = st.button(
            "Fetch historical data",
            type="primary",
            use_container_width=True,
        )
        st.caption(
            "Retrieves daily historical observations; this is not a "
            "real-time streaming feed."
        )

    return ric, start_date, end_date, fetch_clicked


def fetch_requested_data(ric, start_date, end_date):
    """Fetch and store data only when the user clicks the fetch button."""
    st.session_state["live_prices"] = None
    st.session_state["live_request"] = None

    loading_placeholder = st.empty()
    try:
        with loading_placeholder.container():
            render_loading_indicator(ric)

            with st.spinner(f"Fetching {ric} from LSEG Workspace…"):
                open_lseg_session()
                prices = fetch_live_feed(ric, start_date, end_date)

        if prices is None or prices.empty:
            st.error("LSEG returned no price observations.")
            return

        st.session_state["live_prices"] = prices
        st.session_state["live_request"] = (ric, start_date, end_date)

    except Exception as exc:
        st.error(f"Historical data retrieval failed: {exc}")
        traceback.print_exc()

    finally:
        loading_placeholder.empty()


def render_market_overview(ric, prices):
    st.markdown("### Market Overview")
    columns = st.columns(4)

    overview = [
        ("INSTRUMENT", ric),
        ("OBSERVATIONS", f"{len(prices):,}"),
        ("FIRST OBSERVATION", prices.index.min().strftime("%d %b %Y")),
        ("LAST OBSERVATION", prices.index.max().strftime("%d %b %Y")),
    ]

    for column, (label, value) in zip(columns, overview):
        with column:
            st.caption(label)
            st.markdown(f"**{value}**")

    st.divider()


def render_kpis(metrics):
    st.markdown("### Key Risk Indicators")
    columns = st.columns([1.2,1,1,1,1])

    kpis = [
        ("💰 Latest Price", f"{metrics['Latest Price']:,.2f}",
         "Most recent available instrument price."),
        ("📈 Daily Return", format_percentage(metrics["Latest Daily Return"], signed=True),
         "Return over the latest observation interval."),
        ("🌊 Annualized Volatility", format_percentage(metrics["Annualized Volatility"]),
         "Annualized standard deviation of returns."),
        ("📉 Maximum Drawdown", format_percentage(metrics["Maximum Drawdown"]),
         "Largest peak-to-trough decline over the selected period."),
        ("🗓️ Observations", f"{int(metrics['Observations']):,}",
         "Number of price observations used in the analysis."),
    ]

    for column, (label, value, help_text) in zip(columns, kpis):
        with column:
            st.metric(label, value, help=help_text)

    st.caption(
        "Returns and drawdown are expressed as decimals before formatting. "
        "Volatility is annualized using 252 trading days."
    )
    st.divider()


def render_price_chart(ric, prices):
    st.markdown("### Price History")
    price_df = prices.rename("Price").rename_axis("Date").reset_index()

    if price_df.empty or price_df["Price"].dropna().empty:
        st.warning("No valid price observations are available to plot.")
        return

    chart = px.line(
        price_df,
        x="Date",
        y="Price",
        title=f"{ric} · Historical Price",
    )
    chart.update_traces(
        line=dict(color=ACCENT, width=2.5),
        hovertemplate="Date: %{x|%d %b %Y}<br>Price: %{y:,.4f}<extra></extra>",
    )
    chart.update_yaxes(title_text="Price (quoted units)")
    st.plotly_chart(
        style_chart(chart, height=420),
        # use_container_width=True,
        width="stretch",
        key="historical_price_chart",
        config={"displaylogo": False},
    )


def render_returns_chart(returns):
    st.markdown("### Daily Performance")
    valid_returns = returns.dropna()

    if valid_returns.empty:
        st.info("Daily returns are unavailable for this sample.")
        return

    returns_df = (valid_returns * 100).rename("Return").rename_axis("Date").reset_index()
    chart = px.bar(
        returns_df,
        x="Date",
        y="Return",
        title="Daily Percentage Returns",
        color="Return",
        color_continuous_scale=[NEGATIVE, "#334155", POSITIVE],
        color_continuous_midpoint=0,
    )
    chart.update_traces(
        hovertemplate="Date: %{x|%d %b %Y}<br>Return: %{y:.2f}%<extra></extra>"
    )
    chart.update_layout(coloraxis_showscale=False)
    chart.update_yaxes(
        title_text="Return (%)",
        zeroline=True,
        zerolinecolor=MUTED,
    )
    st.plotly_chart(
        style_chart(chart),
        use_container_width=True,
        config={"displaylogo": False},
    )


def render_volatility_chart(rolling_volatility):
    st.markdown("### Rolling Volatility")
    st.caption("20-observation rolling standard deviation, annualized")
    valid = rolling_volatility.dropna()

    if valid.empty:
        st.info(
            "Not enough observations for a complete 20-day rolling volatility "
            "window. Fetch a longer historical period to populate this chart."
        )
        return

    df = (valid * 100).rename("Volatility").rename_axis("Date").reset_index()
    chart = px.line(
        df,
        x="Date",
        y="Volatility",
        title="Annualized Rolling Volatility",
    )
    chart.update_traces(
        line=dict(color=PURPLE, width=2),
        hovertemplate="Date: %{x|%d %b %Y}<br>Volatility: %{y:.2f}%<extra></extra>",
    )
    chart.update_yaxes(title_text="Volatility (%)")
    st.plotly_chart(
        style_chart(chart),
        use_container_width=True,
        config={"displaylogo": False},
    )


def render_drawdown_chart(drawdown):
    st.markdown("### Drawdown")
    st.caption("Decline from the running peak of the wealth index")
    valid = drawdown.dropna()

    if valid.empty:
        st.info("Drawdown is unavailable for the selected sample.")
        return

    df = (valid * 100).rename("Drawdown").rename_axis("Date").reset_index()
    chart = px.area(
        df,
        x="Date",
        y="Drawdown",
        title="Historical Drawdown",
    )
    chart.update_traces(
        line=dict(color=NEGATIVE, width=1.5),
        fillcolor="rgba(248, 113, 113, 0.18)",
        hovertemplate="Date: %{x|%d %b %Y}<br>Drawdown: %{y:.2f}%<extra></extra>",
    )
    chart.update_yaxes(
        title_text="Drawdown (%)",
        zeroline=True,
        zerolinecolor=MUTED,
    )
    st.plotly_chart(
        style_chart(chart),
        use_container_width=True,
        config={"displaylogo": False},
    )


def render_export(prices, ric):
    st.divider()
    with st.expander("Export and inspect data"):
        st.caption("Download the selected instrument's historical prices.")
        csv_data = prices.rename("Price").to_frame().to_csv(index_label="Date")
        st.download_button(
            label="Download price history (CSV)",
            data=csv_data,
            file_name=f"{ric.replace('=', '_')}_prices.csv",
            mime="text/csv",
            use_container_width=True,
        )

        with st.expander("Preview price observations"):
            st.dataframe(
                prices.rename("Price").to_frame(),
                use_container_width=True,
            )


def main():
    apply_theme()
    ric, start_date, end_date, fetch_clicked = render_sidebar()
    render_header()
    st.divider()

    #Dashboard contect remains null until valid data is available
    dashboard_context = None

    #Validate dashboard inputs
    if not ric:
        st.warning("Enter a valid instrument RIC.")

    elif start_date > end_date:
        st.error("Start date should be on or before end date.")

    else:
        #Fetch data only when required
        if fetch_clicked:
            fetch_requested_data(ric, start_date, end_date)

        requested_range = (ric, start_date, end_date)

        if (
            st.session_state.get("live_prices") is None
            or st.session_state.get("live_request") != requested_range
        ):
            st.info("Choose the RIC and date range, then click **Fetch historical data**.")

        else:  

            prices = (
                st.session_state["live_prices"]
                .copy()
                .dropna()
                .sort_index()
            )

            if len(prices) < 2:
                st.error("At least two valid observations are required.")

            else:
                
                render_market_overview(ric, prices)

                results = calculate_metrics(prices)
    
                metrics = results["metrics"]
                returns = results["returns"]
                rolling_volatility = results["rolling_volatility"]
                drawdown = results["drawdown"]

                dashboard_context = {
                    "ric": ric,
                    "start_date": start_date,
                    "end_date": end_date,
                    "first_observation": (
                        prices.index.min().strftime("%Y-%m-%d")
                    ),

                    "last_observation": (
                        prices.index.max().strftime("%Y-%m-%d")
                    ),

                    "metrics": metrics
                }

                #Render the existing dashboard
                render_kpis(metrics)
                render_price_chart(ric, prices)
                render_returns_chart(returns)

                left, right = st.columns(2, gap="large")

                with left:
                    render_volatility_chart(rolling_volatility)

                with right:
                    render_drawdown_chart(drawdown)

                render_export(prices, ric)

    #MarketMate is independent of the dashboard data-fetching flow
    st.divider()
    render_chatbot(
        dashboard_context=dashboard_context
    )


if __name__ == "__main__":
    main()
