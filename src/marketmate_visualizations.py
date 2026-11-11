import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_ui import PURPLE, style_chart


def _render_observation_counts(observation_counts):
    """Display the number of paired observations used for each correlation."""
    if not isinstance(observation_counts, dict) or not observation_counts:
        return

    try:
        counts_df = pd.DataFrame.from_dict(
            observation_counts,
            orient="index",
        )
        counts_df = counts_df.apply(pd.to_numeric, errors="coerce")
    except (TypeError, ValueError):
        st.warning("Pairwise observation counts could not be displayed.")
        return

    with st.expander("View pairwise observation counts"):
        st.dataframe(
            counts_df,
            use_container_width=True,
        )


def _render_heatmap(matrix, title, observation_counts=None):
    """Render an annotated correlation heatmap and its observation counts."""

    if not isinstance(matrix, dict) or not matrix:
        st.info("No correlation matrix is available.")
        _render_observation_counts(observation_counts)
        return

    try:
        # Each outer key represents a row; each inner key represents a column.
        matrix_df = pd.DataFrame.from_dict(
            matrix,
            orient="index",
        )
        matrix_df = matrix_df.apply(pd.to_numeric, errors="coerce")
    except (TypeError, ValueError):
        st.warning("The correlation matrix could not be displayed.")
        _render_observation_counts(observation_counts)
        return

    if matrix_df.empty:
        st.info("The correlation matrix contains no observations.")
        _render_observation_counts(observation_counts)
        return

    # Keep the row and column labels aligned with the supplied matrix.
    matrix_df = matrix_df.astype(float)

    if not matrix_df.notna().any().any():
        st.info(
            "No valid correlation coefficients are available for this "
            "regime. This may occur when the pairwise sample is below the "
            "minimum observation requirement or a return series has "
            "zero variance."
        )
        _render_observation_counts(observation_counts)
        return

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix_df.values,
            x=matrix_df.columns.tolist(),
            y=matrix_df.index.tolist(),
            colorscale="RdBu",
            zmin=-1,
            zmax=1,
            zmid=0,
            colorbar=dict(title="Correlation"),
            hovertemplate=(
                "Asset X: %{x}<br>"
                "Asset Y: %{y}<br>"
                "Correlation: %{z:.3f}"
                "<extra></extra>"
            ),
        )
    )

    # Add coefficients to cells where a valid correlation is available.
    for row_index, row_name in enumerate(matrix_df.index):
        for col_index, col_name in enumerate(matrix_df.columns):
            value = matrix_df.iloc[row_index, col_index]

            if pd.notna(value):
                fig.add_annotation(
                    x=col_name,
                    y=row_name,
                    text=f"{value:.2f}",
                    showarrow=False,
                    font=dict(size=12, color="black"),
                )

    fig.update_layout(
        title=title,
        height=420,
        xaxis_title="",
        yaxis_title="",
    )
    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(
        style_chart(fig, height=420),
        use_container_width=True,
        config={"displaylogo": False},
    )

    _render_observation_counts(observation_counts)


def render_rolling_volatility(result):
    """Render historical rolling annualised volatility."""

    st.markdown("### Historical Volatility")

    if not isinstance(result, dict) or not result.get("success"):
        st.warning("Historical volatility results are unavailable.")
        return

    ric = result.get("ric", "Unknown")
    asset = result.get("asset", ric)
    window = result.get("window", "N/A")
    latest_volatility = result.get("latest_annualized_volatility")

    col1, col2, col3 = st.columns(3)

    with col1:
        if latest_volatility is not None:
            st.metric(
                "Latest Annualised Volatility",
                f"{latest_volatility * 100:.2f}%",
            )
        else:
            st.metric("Latest Annualised Volatility", "N/A")

    with col2:
        st.metric("Observations", result.get("observations", "N/A"))

    with col3:
        st.metric("Rolling Window", f"{window} observations")

    date_range = result.get("date_range", {})
    st.caption(
        f"{asset} ({ric}) · "
        f"{date_range.get('start', 'N/A')} to "
        f"{date_range.get('end', 'N/A')}"
    )

    volatility_data = result.get("rolling_volatility")

    if not isinstance(volatility_data, dict) or not volatility_data:
        st.info(
            "The rolling-volatility time series is unavailable. "
            "Only the latest volatility observation was returned."
        )
        return

    volatility_df = pd.DataFrame(
        list(volatility_data.items()),
        columns=["Date", "Volatility"],
    )

    volatility_df["Date"] = pd.to_datetime(
        volatility_df["Date"],
        errors="coerce",
    )
    volatility_df["Volatility"] = pd.to_numeric(
        volatility_df["Volatility"],
        errors="coerce",
    )

    volatility_df = (
        volatility_df
        .dropna(subset=["Date", "Volatility"])
        .sort_values("Date")
    )

    if volatility_df.empty:
        st.info("No valid rolling-volatility observations to plot.")
        return

    # The source values are decimals; display them as percentages.
    volatility_df["Volatility"] *= 100

    fig = px.line(
        volatility_df,
        x="Date",
        y="Volatility",
        title=f"{asset}: Rolling Annualised Volatility",
    )
    fig.update_traces(
        line=dict(color=PURPLE, width=2),
        hovertemplate=(
            "Date: %{x|%d %b %Y}<br>"
            "Volatility: %{y:.2f}%"
            "<extra></extra>"
        ),
    )
    fig.update_yaxes(title_text="Annualised Volatility (%)")

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True,
        config={"displaylogo": False},
    )


def render_correlation_heatmap(result):
    """Render cross-asset correlations and pairwise observation counts."""

    st.markdown("### Cross-Asset Correlations")

    if not isinstance(result, dict) or not result.get("success"):
        st.warning("Cross-asset correlation results are unavailable.")
        return

    date_range = result.get("date_range", {})
    st.caption(
        f"Historical window: {date_range.get('start', 'N/A')} "
        f"to {date_range.get('end', 'N/A')}"
    )
    st.caption(
        "Pearson correlations calculated using pairwise complete "
        "daily-return observations."
    )

    _render_heatmap(
        matrix=result.get("correlation_matrix"),
        title="Cross-Asset Correlation Matrix",
        observation_counts=result.get("observation_counts"),
    )

    failures = result.get("failures")
    if failures:
        st.warning(
            "Some instruments could not be retrieved. "
            "The analysis uses the successfully retrieved instruments."
        )
        st.write(failures)


def _flatten_dictionary(data, prefix=""):
    """Convert a nested dictionary into metric/value rows."""

    rows = []

    if not isinstance(data, dict):
        return rows

    for key, value in data.items():
        label = f"{prefix} / {key}" if prefix else str(key)

        if isinstance(value, dict):
            rows.extend(
                _flatten_dictionary(value, prefix=label)
            )
        else:
            rows.append({
                "Metric": label,
                "Value": value,
            })

    return rows


def render_stress_analysis(result):
    """Render stress-regime statistics and conditional correlations."""

    st.markdown("### Stress-Regime Analysis")

    if not isinstance(result, dict) or not result.get("success"):
        st.warning("Stress-regime analysis results are unavailable.")
        return

    date_range = result.get("date_range", {})
    indicator = result.get("stress_indicator", {})
    observations = result.get("regime_observations", {})

    st.caption(
        f"Historical window: {date_range.get('start', 'N/A')} "
        f"to {date_range.get('end', 'N/A')}"
    )

    st.caption(
        f"Minimum observations required for correlations: "
        f"{result.get('min_observations', 'N/A')}"
    )

    # Display stress-classification parameters.
    col1, col2, col3 = st.columns(3)

    threshold = indicator.get("annualized_volatility_threshold")

    with col1:
        st.metric(
            "Stress Indicator",
            indicator.get("name", "N/A"),
        )

    with col2:
        if threshold is not None:
            st.metric(
                "Stress Threshold",
                f"{threshold * 100:.2f}%",
            )
        else:
            st.metric("Stress Threshold", "N/A")

    with col3:
        st.metric(
            "Rolling Window",
            f"{indicator.get('window', 'N/A')} observations",
        )

    # Display the number of observations in each regime.
    st.markdown("#### Regime Classification")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Stress Observations",
            observations.get("stress", "N/A"),
        )

    with col2:
        st.metric(
            "Non-Stress Observations",
            observations.get("non_stress", "N/A"),
        )

    with col3:
        st.metric(
            "Total Classified",
            observations.get("total_classified", "N/A"),
        )

    # Display regime-specific return and risk statistics.
    st.markdown("#### Regime Statistics")

    regime_statistics = result.get("regime_statistics", {})
    statistics_rows = _flatten_dictionary(regime_statistics)

    if statistics_rows:
        statistics_df = pd.DataFrame(statistics_rows)
        st.dataframe(
            statistics_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No regime statistics are available.")

    # Display separate conditional correlation matrices.
    st.markdown("#### Conditional Correlations")

    conditional_correlations = result.get(
        "conditional_correlations",
        {},
    )

    if not isinstance(conditional_correlations, dict) or not conditional_correlations:
        st.info("No conditional correlation matrices are available.")
    else:
        for regime, regime_results in conditional_correlations.items():
            regime_title = regime.replace("_", " ").title()

            st.markdown(f"**{regime_title} Regime**")

            if not isinstance(regime_results, dict):
                st.info(
                    f"The {regime_title.lower()} correlation results "
                    "are not in the expected format."
                )
                continue

            _render_heatmap(
                matrix=regime_results.get("correlation_matrix"),
                title=f"{regime_title} Correlations",
                observation_counts=regime_results.get(
                    "observation_counts"
                ),
            )

    failures = result.get("failures")
    if failures:
        st.warning(
            "Some instruments could not be retrieved. "
            "The analysis uses the successfully retrieved instruments."
        )
        st.write(failures)
