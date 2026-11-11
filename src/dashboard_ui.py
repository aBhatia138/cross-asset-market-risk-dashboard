import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Shared visual palette
BG = "#0B1220"
PANEL = "#111C2E"
ACCENT = "#2DD4BF"
TEXT = "#E5EDF7"
MUTED = "#91A1B7"
POSITIVE = "#34D399"
NEGATIVE = "#F87171"
GRID = "#263449"
PURPLE = "#A78BFA"


def apply_theme():
    """Apply the dashboard's global CSS theme."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {BG};
            color: {TEXT};
        }}

        [data-testid="stHeader"] {{
            background-color: {BG};
        }}

        [data-testid="stSidebar"] {{
            background-color: {PANEL};
            border-right: 1px solid {GRID};
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1600px;
        }}

        h1, h2, h3 {{
            color: {TEXT};
            letter-spacing: -0.4px;
        }}

        [data-testid="stCaptionContainer"] {{
            color: {MUTED};
        }}

        /* Glassmorphism KPI cards */
        [data-testid="stMetric"] {{
            background: rgba(17, 28, 46, 0.68);
            border: 1px solid rgba(145, 161, 183, 0.18);
            border-radius: 16px;
            padding: 20px 18px;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
            transition: transform 220ms ease, background 220ms ease,
                        border-color 220ms ease, box-shadow 220ms ease;
        }}

        [data-testid="stMetric"]:hover {{
            transform: translateY(-5px);
            background: rgba(45, 212, 191, 0.10);
            border-color: rgba(45, 212, 191, 0.55);
            box-shadow: 0 10px 30px rgba(0,0,0,0.22),
                        0 0 18px rgba(45,212,191,0.08);
        }}

        [data-testid="stMetricLabel"] {{
            color: {MUTED};
        }}

        [data-testid="stMetricValue"] {{
            color: {TEXT};
            font-weight: 650;
            letter-spacing: -0.5px;
            transition: color 220ms ease;
        }}

        [data-testid="stMetric"]:hover [data-testid="stMetricValue"] {{
            color: {ACCENT};
        }}

        @media (prefers-reduced-motion: reduce) {{
            [data-testid="stMetric"] {{ transition: none; }}
        }}

        div.stButton > button,
        div.stDownloadButton > button {{
            border-radius: 8px;
            font-weight: 600;
            min-height: 42px;
        }}

        div.stButton > button[kind="primary"] {{
            background-color: {ACCENT};
            color: {BG};
            border: none;
        }}

        div.stButton > button[kind="primary"]:hover {{
            background-color: #5EEAD4;
            color: {BG};
            border: none;
        }}

        hr {{
            border-color: {GRID};
        }}

        .dashboard-header {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 12px 0 24px 0;
            margin-bottom: 24px;
            border-bottom: 1px solid rgba(45, 212, 191, 0.22);
        }}

        .brand-logo {{
            width: 88px;
            min-width: 88px;
            height: 88px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 20px;
            background: radial-gradient(circle at 40% 35%,
                rgba(45, 212, 191, 0.15),
                rgba(17, 28, 46, 0.55) 72%);
            border: 1px solid rgba(45, 212, 191, 0.20);
            box-shadow: 0 0 24px rgba(45, 212, 191, 0.07);
        }}

        .brand-logo svg {{
            width: 82px;
            height: 82px;
        }}

        .brand-divider {{
            width: 2px;
            min-width: 2px;
            height: 62px;
            background: linear-gradient(to bottom, transparent, {ACCENT}, transparent);
        }}

        .brand-copy {{ min-width: 0; }}

        .brand-title {{
            color: {TEXT};
            font-size: clamp(1.35rem, 2.5vw, 2rem);
            font-weight: 750;
            letter-spacing: -0.8px;
            line-height: 1.3;
        }}

        .brand-title span {{ color: {ACCENT}; }}

        .brand-subtitle {{
            color: {MUTED};
            font-size: 0.76rem;
            font-weight: 500;
            letter-spacing: 1.4px;
            margin-top: 9px;
            line-height: 1.6;
        }}

        .brand-dot {{
            color: {ACCENT};
            font-size: 0.55rem;
            margin: 0 8px;
            vertical-align: middle;
        }}

        @media (max-width: 600px) {{
            .dashboard-header {{ gap: 12px; }}
            .brand-logo {{
                width: 64px;
                min-width: 64px;
                height: 64px;
            }}
            .brand-logo svg {{ width: 60px; height: 60px; }}
            .brand-subtitle {{
                font-size: 0.62rem;
                letter-spacing: 0.5px;
            }}
            .brand-divider {{ height: 52px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    """Render the custom SVG brand header."""
    st.markdown(
        """
        <div class="dashboard-header">
          <div class="brand-logo">
            <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"
                 role="img" aria-label="Cross-asset market analytics logo">
              <defs>
                <linearGradient id="tealGradient" x1="0%" y1="100%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#0F766E"/>
                  <stop offset="55%" stop-color="#2DD4BF"/>
                  <stop offset="100%" stop-color="#99F6E4"/>
                </linearGradient>
                <radialGradient id="globeGradient">
                  <stop offset="0%" stop-color="#164E63"/>
                  <stop offset="100%" stop-color="#0B1220"/>
                </radialGradient>
                <filter id="logoGlow">
                  <feGaussianBlur stdDeviation="2.2" result="blur"/>
                  <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
              </defs>
              <circle cx="45" cy="43" r="29" fill="url(#globeGradient)"
                      stroke="#2DD4BF" stroke-width="1.6"/>
              <ellipse cx="45" cy="43" rx="13" ry="29" fill="none"
                       stroke="#2DD4BF" stroke-opacity="0.65" stroke-width="1.1"/>
              <ellipse cx="45" cy="43" rx="29" ry="11" fill="none"
                       stroke="#2DD4BF" stroke-opacity="0.65" stroke-width="1.1"/>
              <path d="M18 43 H72 M45 14 V72" fill="none"
                    stroke="#2DD4BF" stroke-opacity="0.45" stroke-width="1"/>
              <g fill="url(#tealGradient)" filter="url(#logoGlow)">
                <rect x="26" y="56" width="7" height="15" rx="1.5"/>
                <rect x="37" y="48" width="7" height="23" rx="1.5"/>
                <rect x="48" y="39" width="7" height="32" rx="1.5"/>
                <rect x="59" y="27" width="7" height="44" rx="1.5"/>
              </g>
              <ellipse cx="46" cy="43" rx="42" ry="15" transform="rotate(-27 46 43)"
                       fill="none" stroke="url(#tealGradient)" stroke-width="3"
                       filter="url(#logoGlow)"/>
              <circle cx="81" cy="22" r="3.5" fill="#99F6E4"/>
            </svg>
          </div>
          <div class="brand-divider"></div>
          <div class="brand-copy">
            <div class="brand-title">CROSS-ASSET <span>MARKET METRICS</span></div>
            <div class="brand-subtitle">HISTORICAL MARKET DATA
              <span class="brand-dot">●</span> QUANTITATIVE ANALYTICS
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_percentage(value, signed=False):
    """Format a decimal return/risk value as a percentage."""
    if value is None or pd.isna(value):
        return "N/A"
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{value * 100:.2f}%"


def style_chart(fig, height=350):
    """Apply consistent Plotly styling to all charts."""
    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Arial", size=12),
        margin=dict(l=45, r=20, t=55, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    return fig


def render_loading_indicator(ric):
    """Render an animated, isolated HTML loading bar."""
    st.markdown(
        f'<div style="color:{MUTED};font-size:0.9rem;margin-bottom:8px;">'
        f'<span style="color:{ACCENT};">●</span> '
        f'Connecting to LSEG Workspace and retrieving <b>{ric}</b>…</div>',
        unsafe_allow_html=True,
    )
    components.html(
        """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
          * { box-sizing: border-box; }
          html, body { margin: 0; padding: 0; background: transparent; }
          .track {
            width: 100%; height: 6px; overflow: hidden; position: relative;
            border-radius: 999px; background: #263449;
          }
          .bar {
            position: absolute; top: 0; bottom: 0; width: 35%;
            border-radius: 999px;
            background: linear-gradient(90deg, #0F766E, #2DD4BF, #99F6E4);
            animation: sweep 1.2s linear infinite;
          }
          @keyframes sweep {
            from { left: -35%; }
            to { left: 100%; }
          }
        </style>
        </head>
        <body><div class="track"><div class="bar"></div></div></body>
        </html>
        """,
        height=18,
        scrolling=False,
    )
