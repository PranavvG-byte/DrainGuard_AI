"""
DrainGuard AI - Premium Live Monitoring Dashboard v2.0
Enhanced with glassmorphism, sparklines, tabbed layout, advanced analytics.

Usage:
    streamlit run dashboard/app.py
"""

import os, sys, time, subprocess, signal
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta


from config.settings import (
    LIVE_DATA_CSV, ALERT_LOG_CSV, SENSOR_DATA_CSV,
    DASHBOARD_REFRESH_SECONDS, DASHBOARD_MAX_POINTS,
    WATER_BLOCKAGE_THRESHOLD, WATER_LEAKAGE_THRESHOLD,
    GAS_WARNING_THRESHOLD, GAS_DANGER_THRESHOLD,
    WATER_LEVEL_NORMAL_LOW, WATER_LEVEL_NORMAL_HIGH,
    RISK_LEVELS, MODEL_PATH,
)

st.set_page_config(
    page_title="DrainGuard AI - Smart Drainage Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: linear-gradient(135deg, #050816 0%, #0a0f24 30%, #0d1530 60%, #080d1f 100%);
}

/* Glassmorphism Header */
.hero-header {
    background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.12) 50%, rgba(59,130,246,0.08) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 20px;
    padding: 1.8rem 2.5rem;
    margin-bottom: 1.8rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(59,130,246,0.1), inset 0 1px 0 rgba(255,255,255,0.05);
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(59,130,246,0.06) 0%, transparent 50%);
    animation: headerShimmer 8s ease-in-out infinite;
}
@keyframes headerShimmer {
    0%,100% { transform: translate(0,0); }
    50% { transform: translate(5%,2%); }
}
.hero-title {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #60a5fa);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientText 4s ease infinite;
    margin: 0;
    position: relative;
    z-index: 1;
}
@keyframes gradientText {
    0%{background-position:0%50%}50%{background-position:100%50%}100%{background-position:0%50%}
}
.hero-sub {
    color: #94a3b8;
    margin: 0.3rem 0 0 0;
    font-size: 0.95rem;
    font-weight: 400;
    position: relative;
    z-index: 1;
}
.hero-status {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.pulse-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse 2s infinite;
}
.pulse-dot.green { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
.pulse-dot.red { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
.pulse-dot.orange { background: #f97316; box-shadow: 0 0 8px #f97316; }
@keyframes pulse {
    0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)}
}

/* Glass KPI Cards */
.glass-kpi {
    background: linear-gradient(145deg, rgba(30,41,59,0.6), rgba(15,23,42,0.8));
    backdrop-filter: blur(12px);
    border: 1px solid rgba(100,116,139,0.15);
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}
.glass-kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.glass-kpi:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(59,130,246,0.15);
    border-color: rgba(59,130,246,0.3);
}
.glass-kpi.water::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.glass-kpi.gas::before { background: linear-gradient(90deg, #a855f7, #c084fc); }
.glass-kpi.risk::before { background: linear-gradient(90deg, #f97316, #fb923c); }
.glass-kpi.anomaly::before { background: linear-gradient(90deg, #ef4444, #f87171); }
.glass-kpi.readings::before { background: linear-gradient(90deg, #22c55e, #4ade80); }

.kpi-icon { font-size: 1.5rem; margin-bottom: 0.2rem; }
.kpi-label {
    color: #94a3b8;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}
.kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0.2rem 0;
    line-height: 1.1;
}
.kpi-unit {
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 500;
}
.sparkline-container {
    height: 35px;
    margin-top: 0.3rem;
    opacity: 0.6;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(15,23,42,0.5);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(100,116,139,0.1);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.3px;
    color: #94a3b8;
    padding: 10px 20px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.15)) !important;
    color: #60a5fa !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
}

/* Alert Cards */
.alert-card-v2 {
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    border-left: 4px solid;
    backdrop-filter: blur(8px);
    transition: all 0.2s ease;
}
.alert-card-v2:hover { transform: translateX(4px); }
.alert-critical {
    background: rgba(220,38,38,0.08);
    border-color: #dc2626;
}
.alert-high {
    background: rgba(239,68,68,0.06);
    border-color: #ef4444;
}
.alert-moderate {
    background: rgba(249,115,22,0.06);
    border-color: #f97316;
}
.alert-low {
    background: rgba(234,179,8,0.06);
    border-color: #eab308;
}
.alert-meta {
    color: #64748b;
    font-size: 0.75rem;
    margin-top: 0.3rem;
}

/* System Health */
.health-card {
    background: rgba(30,41,59,0.4);
    border: 1px solid rgba(100,116,139,0.1);
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
.health-label { color: #94a3b8; font-size: 0.8rem; font-weight: 500; }
.health-value { color: #e2e8f0; font-size: 1.1rem; font-weight: 700; }
.health-bar {
    height: 6px;
    border-radius: 3px;
    background: rgba(100,116,139,0.2);
    margin-top: 0.4rem;
    overflow: hidden;
}
.health-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

/* Section Headers */
.section-header {
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 700;
    margin: 1rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f24 0%, #050816 100%);
    border-right: 1px solid rgba(100,116,139,0.1);
}

/* Hide Streamlit defaults */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

[data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ─── Data Loading ────────────────────────────────────────────
def load_live_data(ttl_seconds=DASHBOARD_REFRESH_SECONDS):
    """Load live data with configurable cache TTL (#13: respects slider)."""
    @st.cache_data(ttl=ttl_seconds)
    def _load(ttl_key):
        try:
            if os.path.exists(LIVE_DATA_CSV):
                df = pd.read_csv(LIVE_DATA_CSV)
                if len(df) > 0:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    return df.tail(DASHBOARD_MAX_POINTS)
        except Exception:
            pass
        return pd.DataFrame()
    return _load(ttl_seconds)


def load_alerts(ttl_seconds=DASHBOARD_REFRESH_SECONDS):
    """Load alerts with configurable cache TTL (#13: respects slider)."""
    @st.cache_data(ttl=ttl_seconds)
    def _load(ttl_key):
        try:
            if os.path.exists(ALERT_LOG_CSV):
                df = pd.read_csv(ALERT_LOG_CSV)
                if len(df) > 0:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    return df.tail(50)
        except Exception:
            pass
        return pd.DataFrame()
    return _load(ttl_seconds)


@st.cache_data(ttl=60)
def load_training_data():
    try:
        if os.path.exists(SENSOR_DATA_CSV):
            df = pd.read_csv(SENSOR_DATA_CSV)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


# ─── Sparkline Generator ────────────────────────────────────
def make_sparkline_svg(values, color="#3b82f6", width=120, height=30):
    if len(values) < 2:
        return ""
    vals = list(values[-30:])
    mn, mx = min(vals), max(vals)
    rng = mx - mn if mx != mn else 1
    points = []
    for i, v in enumerate(vals):
        x = (i / (len(vals) - 1)) * width
        y = height - ((v - mn) / rng) * (height - 4) - 2
        points.append(f"{x:.1f},{y:.1f}")
    path = " ".join(points)
    gradient_id = f"sg_{hash(color) % 10000}"
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
        <defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
        </linearGradient></defs>
        <polyline fill="url(#{gradient_id})" stroke="none" points="{points[0]} {path} {points[-1]} {width},{ height} 0,{height}"/>
        <polyline fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" points="{path}"/>
    </svg>'''


# ─── Chart: Plot Layout Helper ───────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,15,36,0.5)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(l=0, r=0, t=45, b=0),
    hovermode="x unified",
    xaxis=dict(gridcolor="rgba(51,65,85,0.2)", color="#64748b", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="rgba(51,65,85,0.2)", color="#64748b", showgrid=True, zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color="#94a3b8", size=10)),
)


def create_water_level_chart(df):
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=WATER_BLOCKAGE_THRESHOLD,
                  fillcolor="rgba(239,68,68,0.06)", line_width=0,
                  annotation_text="⚠ Blockage", annotation_position="top left",
                  annotation_font=dict(color="#ef4444", size=9))
    fig.add_hrect(y0=WATER_LEAKAGE_THRESHOLD, y1=200,
                  fillcolor="rgba(249,115,22,0.06)", line_width=0,
                  annotation_text="⚠ Leakage", annotation_position="bottom left",
                  annotation_font=dict(color="#f97316", size=9))
    fig.add_hrect(y0=WATER_LEVEL_NORMAL_LOW, y1=WATER_LEVEL_NORMAL_HIGH,
                  fillcolor="rgba(34,197,94,0.04)", line_width=0)

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["water_level_cm"],
        mode="lines", line=dict(color="#3b82f6", width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.06)",
        name="Water Level",
        hovertemplate="<b>%{x}</b><br>Water: %{y:.1f} cm<extra></extra>",
    ))

    # Trend prediction (SMA)
    if len(df) > 20:
        sma = df["water_level_cm"].rolling(10, min_periods=1).mean()
        last_trend = sma.iloc[-10:].values
        slope = (last_trend[-1] - last_trend[0]) / len(last_trend)
        future_x = pd.date_range(df["timestamp"].iloc[-1], periods=15, freq="2s")
        future_y = [last_trend[-1] + slope * i for i in range(15)]
        fig.add_trace(go.Scatter(
            x=future_x, y=future_y,
            mode="lines", line=dict(color="#60a5fa", width=1.5, dash="dot"),
            name="Trend", showlegend=True,
        ))

    anomalies = df[df["is_anomaly"] == 1]
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies["timestamp"], y=anomalies["water_level_cm"],
            mode="markers",
            marker=dict(color="#ef4444", size=9, symbol="diamond",
                       line=dict(color="#fca5a5", width=1.5)),
            name="Anomaly",
        ))

    fig.update_layout(**CHART_LAYOUT, height=320,
                      title=dict(text="💧 Water Level (cm)", font=dict(size=13, color="#e2e8f0")),
                      yaxis_title="cm")
    return fig


def create_gas_level_chart(df):
    fig = go.Figure()
    fig.add_hrect(y0=GAS_DANGER_THRESHOLD, y1=4095,
                  fillcolor="rgba(239,68,68,0.08)", line_width=0,
                  annotation_text="☠ DANGER", annotation_position="top left",
                  annotation_font=dict(color="#ef4444", size=9))
    fig.add_hrect(y0=GAS_WARNING_THRESHOLD, y1=GAS_DANGER_THRESHOLD,
                  fillcolor="rgba(234,179,8,0.05)", line_width=0,
                  annotation_text="⚠ Warning", annotation_position="top left",
                  annotation_font=dict(color="#eab308", size=9))

    # Color-code markers by gas level (#6: removed unused colors list)
    marker_colors = [
        "#ef4444" if v > GAS_DANGER_THRESHOLD
        else "#eab308" if v > GAS_WARNING_THRESHOLD
        else "#a855f7"
        for v in df["gas_level"]
    ]

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["gas_level"],
        mode="lines+markers",
        line=dict(color="#a855f7", width=2, shape="spline"),
        marker=dict(color=marker_colors, size=3),
        fill="tozeroy", fillcolor="rgba(168,85,247,0.05)",
        name="Gas Level",
        hovertemplate="<b>%{x}</b><br>Gas: %{y} ADC<extra></extra>",
    ))

    anomalies = df[df["is_anomaly"] == 1]
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies["timestamp"], y=anomalies["gas_level"],
            mode="markers",
            marker=dict(color="#ef4444", size=9, symbol="diamond",
                       line=dict(color="#fca5a5", width=1.5)),
            name="Anomaly",
        ))

    fig.update_layout(**CHART_LAYOUT, height=320,
                      title=dict(text="🌫️ Gas Concentration (ADC)", font=dict(size=13, color="#e2e8f0")),
                      yaxis_title="ADC")
    return fig


def create_risk_gauge(risk_score, risk_level):
    color = RISK_LEVELS.get(risk_level, {}).get("color", "#64748b")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        number={"suffix": "%", "font": {"size": 48, "color": color, "family": "Inter"}},
        title={"text": "Risk Score", "font": {"size": 14, "color": "#94a3b8"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#1e293b",
                     "dtick": 25, "tickfont": {"color": "#475569", "size": 10}},
            "bar": {"color": color, "thickness": 0.85},
            "bgcolor": "#0f172a",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "rgba(34,197,94,0.08)"},
                {"range": [25, 50], "color": "rgba(234,179,8,0.08)"},
                {"range": [50, 75], "color": "rgba(249,115,22,0.08)"},
                {"range": [75, 90], "color": "rgba(239,68,68,0.08)"},
                {"range": [90, 100], "color": "rgba(220,38,38,0.12)"},
            ],
            "threshold": {"line": {"color": "#f97316", "width": 3}, "thickness": 0.8, "value": 75},
        },
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def create_risk_timeline(df):
    if "risk_score" not in df.columns:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["risk_score"],
        mode="lines", fill="tozeroy",
        fillcolor="rgba(239,68,68,0.04)",
        line=dict(color="#ef4444", width=2, shape="spline"),
        name="Risk", hovertemplate="<b>%{x}</b><br>Risk: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=75, line_dash="dash", line_color="rgba(239,68,68,0.4)",
                  annotation_text="HIGH", annotation_font=dict(color="#ef4444", size=9))
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(249,115,22,0.3)",
                  annotation_text="MODERATE", annotation_font=dict(color="#f97316", size=9))
    layout = {**CHART_LAYOUT}
    layout["yaxis"] = dict(range=[0, 105], title="%", gridcolor="rgba(51,65,85,0.2)", color="#64748b")
    fig.update_layout(**layout, height=260,
                      title=dict(text="📈 Risk Timeline (%)", font=dict(size=13, color="#e2e8f0")))
    return fig


def create_anomaly_distribution(df):
    if "anomaly_type" not in df.columns:
        return go.Figure()
    anomalies = df[df["is_anomaly"] == 1]
    if len(anomalies) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No anomalies", x=0.5, y=0.5, showarrow=False,
                          font=dict(color="#475569", size=14))
        fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    counts = anomalies["anomaly_type"].value_counts()
    colors_map = {"BLOCKAGE": "#3b82f6", "LEAKAGE": "#f97316",
                  "GAS_HAZARD": "#a855f7", "FLOOD_RISK": "#ef4444", "NORMAL": "#22c55e"}

    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.6,
        marker=dict(colors=[colors_map.get(t, "#64748b") for t in counts.index],
                    line=dict(color="#0a0f24", width=2)),
        textfont=dict(color="#e2e8f0", size=11),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0),
                      paper_bgcolor="rgba(0,0,0,0)",
                      title=dict(text="🎯 Anomaly Types", font=dict(size=13, color="#e2e8f0")),
                      legend=dict(font=dict(color="#94a3b8", size=10)))
    return fig


def create_correlation_scatter(df):
    if len(df) < 2:
        return go.Figure()
    fig = go.Figure()
    normal = df[df["is_anomaly"] == 0] if "is_anomaly" in df.columns else df
    anomalies = df[df["is_anomaly"] == 1] if "is_anomaly" in df.columns else pd.DataFrame()

    fig.add_trace(go.Scatter(
        x=normal["water_level_cm"], y=normal["gas_level"],
        mode="markers", marker=dict(color="#3b82f6", size=5, opacity=0.4),
        name="Normal", hovertemplate="Water: %{x:.1f}cm<br>Gas: %{y}<extra></extra>",
    ))
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies["water_level_cm"], y=anomalies["gas_level"],
            mode="markers", marker=dict(color="#ef4444", size=8, opacity=0.8,
                                        symbol="diamond", line=dict(color="#fca5a5", width=1)),
            name="Anomaly",
        ))
    fig.update_layout(**CHART_LAYOUT, height=320,
                      title=dict(text="🔗 Sensor Correlation", font=dict(size=13, color="#e2e8f0")),
                      xaxis_title="Water Level (cm)", yaxis_title="Gas Level (ADC)")
    return fig


def create_sensor_heatmap(df):
    if len(df) < 10 or "timestamp" not in df.columns:
        return go.Figure()
    df_h = df.copy()
    df_h["minute"] = df_h["timestamp"].dt.minute
    df_h["time_bin"] = df_h["timestamp"].dt.strftime("%H:%M")

    # Create bins of readings (#7: removed unused anomaly_count agg)
    agg_dict = {
        "water_mean": ("water_level_cm", "mean"),
        "gas_mean": ("gas_level", "mean"),
    }
    bins = df_h.groupby("time_bin").agg(**agg_dict).tail(30)

    fig = go.Figure(go.Heatmap(
        x=bins.index,
        y=["Water Level", "Gas Level"],
        z=[bins["water_mean"].values, bins["gas_mean"].values],
        colorscale=[[0, "#0f172a"], [0.3, "#1e3a5f"], [0.6, "#3b82f6"], [0.8, "#f97316"], [1, "#ef4444"]],
        hovertemplate="Time: %{x}<br>%{y}: %{z:.1f}<extra></extra>",
    ))
    layout = {**CHART_LAYOUT, "yaxis": dict(gridcolor="rgba(51,65,85,0.2)", color="#64748b")}
    fig.update_layout(**layout, height=200,
                      title=dict(text="🗺️ Sensor Heatmap", font=dict(size=13, color="#e2e8f0")))
    return fig


# ─── Sidebar ─────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🛡️ DrainGuard AI")
        st.markdown('<p style="color:#64748b;font-size:0.8rem;margin-top:-10px;">Smart Drainage Monitor v2.0</p>',
                    unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("### 📊 Data Source")
        data_mode = st.radio("View Mode", ["Live Data", "Training Data"], index=0,
                            help="Live: real-time from backend | Training: historical dataset")
        st.markdown("---")

        st.markdown("### ⚙️ Settings")
        refresh_rate = st.slider("Refresh Rate (sec)", 1, 10, DASHBOARD_REFRESH_SECONDS)
        max_points = st.slider("Max Chart Points", 50, 500, DASHBOARD_MAX_POINTS, step=50)
        st.markdown("---")

        st.markdown("### 🚀 Backend Control")
        if "backend_process" not in st.session_state:
            st.session_state.backend_process = None

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶ Start", use_container_width=True):
                try:
                    proc = subprocess.Popen(
                        [sys.executable, "backend/app.py", "--mode", "simulator"],
                        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                    )
                    st.session_state.backend_process = proc
                    st.success("Backend started!")
                except Exception as e:
                    st.error(f"Failed: {e}")
        with col2:
            if st.button("⏹ Stop", use_container_width=True):
                if st.session_state.backend_process:
                    try:
                        st.session_state.backend_process.terminate()
                        st.session_state.backend_process = None
                        st.info("Backend stopped")
                    except Exception:
                        pass

        is_online = st.session_state.backend_process and st.session_state.backend_process.poll() is None
        status_class = "green" if is_online else "red"
        status_text = "ONLINE" if is_online else "OFFLINE"
        st.markdown(f'''<div style="display:flex;align-items:center;gap:8px;margin:8px 0;">
            <span class="pulse-dot {status_class}"></span>
            <span style="color:{"#22c55e" if is_online else "#ef4444"};font-weight:600;font-size:0.85rem;">{status_text}</span>
        </div>''', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.markdown(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
        if os.path.exists(LIVE_DATA_CSV):
            size = os.path.getsize(LIVE_DATA_CSV) / 1024
            st.markdown(f"**Live CSV:** {size:.1f} KB")
        if os.path.exists(MODEL_PATH):
            model_size = os.path.getsize(MODEL_PATH) / 1024
            st.markdown(f"**Model:** {model_size:.0f} KB")

        # Data export
        st.markdown("---")
        st.markdown("### 📥 Export")
        if os.path.exists(LIVE_DATA_CSV):
            with open(LIVE_DATA_CSV, "r") as f:
                st.download_button("📄 Download Live Data", f.read(), "drainguard_live_data.csv", "text/csv",
                                  use_container_width=True)
        if os.path.exists(ALERT_LOG_CSV):
            with open(ALERT_LOG_CSV, "r") as f:
                st.download_button("🚨 Download Alerts", f.read(), "drainguard_alerts.csv", "text/csv",
                                  use_container_width=True)

        return data_mode, refresh_rate, max_points


# ─── Main Layout ─────────────────────────────────────────────
def main():
    data_mode, refresh_rate, max_points = render_sidebar()

    # Load data (#13: pass refresh_rate so cache TTL matches slider)
    if data_mode == "Live Data":
        df = load_live_data(ttl_seconds=refresh_rate)
        data_label = "LIVE"
    else:
        df = load_training_data()
        data_label = "HISTORICAL"
    alerts_df = load_alerts(ttl_seconds=refresh_rate)

    # Compute KPI values
    if not df.empty:
        latest = df.iloc[-1]
        water_val = latest.get("water_level_cm", 0)
        gas_val = latest.get("gas_level", 0)
        risk_val = latest.get("risk_score", 0) if "risk_score" in df.columns else 0
        risk_level = latest.get("risk_level", "NORMAL") if "risk_level" in df.columns else "NORMAL"
        total_anomalies = int(df["is_anomaly"].sum()) if "is_anomaly" in df.columns else 0
    else:
        water_val = gas_val = risk_val = total_anomalies = 0
        risk_level = "NORMAL"

    # Risk-based header glow
    if risk_val >= 75:
        pulse_class, pulse_label = "red", "HIGH RISK"
    elif risk_val >= 50:
        pulse_class, pulse_label = "orange", "MODERATE"
    else:
        pulse_class, pulse_label = "green", "NORMAL"

    # Hero Header
    st.markdown(f"""
    <div class="hero-header">
        <div style="display:flex;justify-content:space-between;align-items:center;position:relative;z-index:1;">
            <div>
                <h1 class="hero-title">🛡️ DrainGuard AI</h1>
                <p class="hero-sub">Smart Urban Drainage Monitoring & Flood Risk Prediction</p>
            </div>
            <div class="hero-status">
                <span class="pulse-dot {pulse_class}"></span>
                <span style="color:#94a3b8;font-weight:600;font-size:0.85rem;">{pulse_label}</span>
                <span style="color:#475569;font-size:0.8rem;margin-left:12px;">
                    {datetime.now().strftime('%H:%M:%S')} • {len(df):,} readings
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.info("📡 No data available. Start the backend using **▶ Start** in the sidebar, or switch to **Training Data**.")
        training_df = load_training_data()
        if not training_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(create_water_level_chart(training_df.tail(500)), use_container_width=True)
            with c2:
                st.plotly_chart(create_gas_level_chart(training_df.tail(500)), use_container_width=True)
        return

    # Color coding
    water_color = "#ef4444" if water_val < WATER_BLOCKAGE_THRESHOLD else "#f97316" if water_val > WATER_LEAKAGE_THRESHOLD else "#3b82f6"
    gas_color = "#ef4444" if gas_val > GAS_DANGER_THRESHOLD else "#eab308" if gas_val > GAS_WARNING_THRESHOLD else "#a855f7"
    risk_color = RISK_LEVELS.get(risk_level, {}).get("color", "#64748b")

    # Sparklines
    water_spark = make_sparkline_svg(df["water_level_cm"].values, water_color) if len(df) > 2 else ""
    gas_spark = make_sparkline_svg(df["gas_level"].values, gas_color) if len(df) > 2 else ""
    risk_spark = make_sparkline_svg(df["risk_score"].values, risk_color) if "risk_score" in df.columns and len(df) > 2 else ""

    # ─── KPI Row ─────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    for col, cls, icon, label, val, unit, color, spark in [
        (k1, "water", "💧", "WATER LEVEL", f"{water_val:.1f}", "cm", water_color, water_spark),
        (k2, "gas", "🌫️", "GAS LEVEL", f"{int(gas_val)}", "ADC", gas_color, gas_spark),
        (k3, "risk", "⚠️", "RISK SCORE", f"{risk_val:.0f}%", risk_level, risk_color, risk_spark),
        (k4, "anomaly", "🚨", "ANOMALIES", str(total_anomalies), "detected", "#ef4444", ""),
        (k5, "readings", "📊", "READINGS", f"{len(df):,}", data_label, "#22c55e", ""),
    ]:
        with col:
            st.markdown(f"""
            <div class="glass-kpi {cls}">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{color}">{val}</div>
                <div class="kpi-unit">{unit}</div>
                <div class="sparkline-container">{spark}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Tabbed Layout ───────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📡 Live Monitor", "📊 Analytics", "🚨 Alerts", "🔧 System"])

    # ─── TAB 1: Live Monitor ─────────────────────────────
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(create_water_level_chart(df.tail(max_points)), use_container_width=True)
        with c2:
            st.plotly_chart(create_gas_level_chart(df.tail(max_points)), use_container_width=True)

        r1, r2, r3 = st.columns([2, 3, 2])
        with r1:
            st.plotly_chart(create_risk_gauge(risk_val, risk_level), use_container_width=True)
        with r2:
            st.plotly_chart(create_risk_timeline(df.tail(max_points)), use_container_width=True)
        with r3:
            st.plotly_chart(create_anomaly_distribution(df), use_container_width=True)

    # ─── TAB 2: Analytics ────────────────────────────────
    with tab2:
        st.markdown('<div class="section-header">🔬 Deep Analysis</div>', unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            st.plotly_chart(create_correlation_scatter(df.tail(max_points)), use_container_width=True)
        with a2:
            st.plotly_chart(create_sensor_heatmap(df.tail(max_points)), use_container_width=True)

        # Stats summary
        st.markdown('<div class="section-header">📋 Statistical Summary</div>', unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Avg Water Level", f"{df['water_level_cm'].mean():.1f} cm",
                      f"σ = {df['water_level_cm'].std():.1f}")
        with s2:
            st.metric("Avg Gas Level", f"{df['gas_level'].mean():.0f} ADC",
                      f"σ = {df['gas_level'].std():.0f}")
        with s3:
            anomaly_rate = (df["is_anomaly"].sum() / len(df) * 100) if "is_anomaly" in df.columns else 0
            st.metric("Anomaly Rate", f"{anomaly_rate:.1f}%", f"{int(df['is_anomaly'].sum())} events" if "is_anomaly" in df.columns else "N/A")
        with s4:
            time_span = (df["timestamp"].max() - df["timestamp"].min()).total_seconds() / 60 if len(df) > 1 else 0
            st.metric("Time Span", f"{time_span:.0f} min", f"{len(df):,} samples")

        # Data table
        with st.expander("📄 Raw Data (last 20 readings)", expanded=False):
            st.dataframe(df.tail(20).iloc[::-1], use_container_width=True, height=300)

    # ─── TAB 3: Alerts ───────────────────────────────────
    with tab3:
        st.markdown('<div class="section-header">🚨 Alert History</div>', unsafe_allow_html=True)

        if not alerts_df.empty:
            # Alert summary
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                st.metric("Total Alerts", len(alerts_df))
            with ac2:
                critical = len(alerts_df[alerts_df["risk_level"].isin(["CRITICAL", "HIGH"])]) if "risk_level" in alerts_df.columns else 0
                st.metric("Critical/High", critical)
            with ac3:
                if len(alerts_df) > 0:
                    last_ts = pd.to_datetime(alerts_df["timestamp"].iloc[-1]).strftime("%H:%M:%S")
                    st.metric("Last Alert", last_ts)

            st.markdown("---")

            for _, row in alerts_df.tail(15).iloc[::-1].iterrows():
                severity = str(row.get("risk_level", "LOW")).lower()
                css_class = f"alert-{severity}" if severity in ["critical", "high", "moderate"] else "alert-low"
                icon = {"critical": "🔴", "high": "🟠", "moderate": "🟡"}.get(severity, "🟢")
                ts = pd.to_datetime(row["timestamp"]).strftime("%H:%M:%S") if pd.notna(row.get("timestamp")) else "N/A"

                st.markdown(f"""
                <div class="alert-card-v2 {css_class}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:700;color:#e2e8f0;">
                            {icon} {row.get('anomaly_type', 'UNKNOWN')}
                        </span>
                        <span style="color:#94a3b8;font-size:0.8rem;">{ts}</span>
                    </div>
                    <div class="alert-meta">
                        Risk: <b style="color:{RISK_LEVELS.get(severity.upper(), {}).get('color', '#64748b')}">{row.get('risk_score', 0):.0f}%</b> •
                        Water: {row.get('water_level_cm', 0):.1f}cm •
                        Gas: {row.get('gas_level', 0)}
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem;margin-top:4px;">{row.get('message', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No alerts recorded. System operating normally.")

    # ─── TAB 4: System ───────────────────────────────────
    with tab4:
        st.markdown('<div class="section-header">🔧 System Health</div>', unsafe_allow_html=True)

        h1, h2, h3 = st.columns(3)
        with h1:
            model_exists = os.path.exists(MODEL_PATH)
            st.markdown(f"""
            <div class="health-card">
                <div class="health-label">AI Model</div>
                <div class="health-value">{'✅ Loaded' if model_exists else '❌ Missing'}</div>
                <div style="color:#64748b;font-size:0.75rem;margin-top:4px;">
                    {'Isolation Forest – 200 estimators' if model_exists else 'Run train_model.py first'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with h2:
            pipeline_status = "Active" if not df.empty and data_mode == "Live Data" else "Idle"
            st.markdown(f"""
            <div class="health-card">
                <div class="health-label">Data Pipeline</div>
                <div class="health-value">{'🟢' if pipeline_status == 'Active' else '⚪'} {pipeline_status}</div>
                <div style="color:#64748b;font-size:0.75rem;margin-top:4px;">
                    {f'{len(df):,} readings processed' if not df.empty else 'No data flowing'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with h3:
            st.markdown(f"""
            <div class="health-card">
                <div class="health-label">Dashboard</div>
                <div class="health-value">🟢 Running</div>
                <div style="color:#64748b;font-size:0.75rem;margin-top:4px;">
                    Refresh: {refresh_rate}s • Max points: {max_points}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Model performance (if available)
        st.markdown('<div class="section-header">📊 Model Training Stats</div>', unsafe_allow_html=True)
        try:
            import joblib
            model_pkg = joblib.load(MODEL_PATH)
            stats = model_pkg.get("training_stats", {})
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Training Samples", f"{stats.get('samples', 'N/A'):,}")
            with m2:
                st.metric("Precision", f"{stats.get('precision', 0):.1%}")
            with m3:
                st.metric("Recall", f"{stats.get('recall', 0):.1%}")
            with m4:
                st.metric("Anomalies Detected", stats.get("anomalies_detected", "N/A"))

            st.markdown(f"""
            **Features:** {', '.join(model_pkg.get('feature_names', []))}
            **Rolling Window:** {model_pkg.get('rolling_window', 'N/A')} samples
            """)
        except Exception:
            st.warning("Model stats unavailable. Train a model first.")

        # File system info
        st.markdown('<div class="section-header">💾 Storage</div>', unsafe_allow_html=True)
        files_info = [
            ("Live Data CSV", LIVE_DATA_CSV),
            ("Alert Log CSV", ALERT_LOG_CSV),
            ("Training Data CSV", SENSOR_DATA_CSV),
            ("Model File", MODEL_PATH),
        ]
        for name, path in files_info:
            exists = os.path.exists(path)
            size = f"{os.path.getsize(path)/1024:.1f} KB" if exists else "—"
            status = "✅" if exists else "❌"
            st.markdown(f"{status} **{name}**: `{os.path.basename(path)}` ({size})")

    # ─── Auto Refresh (#4: non-blocking refresh) ─────────
    if data_mode == "Live Data":
        import streamlit.components.v1 as components
        # Use a short JS timer to trigger rerun without blocking the server thread
        components.html(
            f"<script>setTimeout(() => window.parent.postMessage({{type: 'streamlit:rerun'}}, '*'), {refresh_rate * 1000});</script>",
            height=0,
        )


if __name__ == "__main__":
    main()
