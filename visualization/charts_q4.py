"""
Q4: Valuation Charts
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import COLOR_PALETTE, CHART_HEIGHT
from utils.constants import *


def create_percentile_timeseries(df: pd.DataFrame,
                                 metric: str = PE,
                                 ticker: str = "") -> go.Figure:
    """
    Create dual-axis chart: metric value and percentile over time

    Args:
        df: DataFrame with valuation data
        metric: Valuation metric (PE, PB, PCFS)
        ticker: Ticker name

    Returns:
        Plotly figure
    """
    percentile_col = f'{metric}_percentile'

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add metric value
    fig.add_trace(
        go.Scatter(
            x=df[DATE],
            y=df[metric],
            name=metric.upper(),
            line=dict(color=COLOR_PALETTE['primary'], width=2)
        ),
        secondary_y=False
    )

    # Add percentile with colored zones
    if percentile_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df[DATE],
                y=df[percentile_col],
                name=f'{metric.upper()} Percentile',
                line=dict(color=COLOR_PALETTE['secondary'], width=2)
            ),
            secondary_y=True
        )

        # Add zone shading
        fig.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.1,
                     layer="below", line_width=0, secondary_y=True,
                     annotation_text="Cheap", annotation_position="right")
        fig.add_hrect(y0=40, y1=60, fillcolor="gray", opacity=0.1,
                     layer="below", line_width=0, secondary_y=True,
                     annotation_text="Fair", annotation_position="right")
        fig.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.1,
                     layer="below", line_width=0, secondary_y=True,
                     annotation_text="Expensive", annotation_position="right")

    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text=f"{metric.upper()} Value", secondary_y=False)
    fig.update_yaxes(title_text="Percentile (%)", secondary_y=True)

    fig.update_layout(
        title=f"{ticker} - {metric.upper()} Value and Historical Percentile",
        height=CHART_HEIGHT,
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


def create_decile_returns_chart(decile_stats: pd.DataFrame,
                                metric: str = PE,
                                ticker: str = "") -> go.Figure:
    """
    Create bar chart of returns by valuation decile

    Args:
        decile_stats: DataFrame with decile statistics
        metric: Valuation metric
        ticker: Ticker name

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Color bars by return (green for positive, red for negative)
    colors = ['green' if x > 0 else 'red' for x in decile_stats['mean']]

    fig.add_trace(go.Bar(
        x=decile_stats[DECILE],
        y=decile_stats['mean'],
        marker_color=colors,
        text=decile_stats['mean'].apply(lambda x: f"{x:.2%}"),
        textposition='outside',
        name='Mean Return'
    ))

    fig.update_layout(
        title=f"{ticker} - Forward Returns by {metric.upper()} Percentile Decile",
        xaxis_title=f"{metric.upper()} Percentile Decile (D1=0-10%, D10=90-100%)",
        yaxis_title="Mean Forward Return",
        yaxis_tickformat='.2%',
        height=CHART_HEIGHT,
        template='plotly_white'
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return fig


def create_valuation_gauge(current_percentile: float,
                           metric: str = PE) -> go.Figure:
    """
    Create gauge chart showing current percentile position

    Args:
        current_percentile: Current percentile value
        metric: Valuation metric

    Returns:
        Plotly figure
    """
    # Determine zone color
    if current_percentile <= 20:
        zone_color = "green"
        zone_text = "Very Cheap"
    elif current_percentile <= 40:
        zone_color = "lightgreen"
        zone_text = "Cheap"
    elif current_percentile <= 60:
        zone_color = "gray"
        zone_text = "Fair"
    elif current_percentile <= 80:
        zone_color = "orange"
        zone_text = "Expensive"
    else:
        zone_color = "red"
        zone_text = "Very Expensive"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_percentile,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{metric.upper()} Percentile<br><span style='font-size:0.8em'>{zone_text}</span>"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': zone_color},
            'steps': [
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 40], 'color': "lightyellow"},
                {'range': [40, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "lightsalmon"},
                {'range': [80, 100], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': current_percentile
            }
        }
    ))

    fig.update_layout(
        height=400,
        template='plotly_white'
    )

    return fig


def create_zone_comparison_chart(cheap_return: float,
                                 expensive_return: float,
                                 metric: str = PE) -> go.Figure:
    """
    Compare returns in cheap vs expensive zones

    Args:
        cheap_return: Mean return in cheap zone (0-20%)
        expensive_return: Mean return in expensive zone (80-100%)
        metric: Valuation metric

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=['Cheap Zone<br>(0-20%)', 'Expensive Zone<br>(80-100%)'],
        y=[cheap_return, expensive_return],
        marker_color=['green', 'red'],
        text=[f"{cheap_return:.2%}", f"{expensive_return:.2%}"],
        textposition='outside'
    ))

    spread = cheap_return - expensive_return

    fig.update_layout(
        title=f"{metric.upper()} - Cheap vs Expensive Zone Returns<br><sub>Spread: {spread:.2%}</sub>",
        yaxis_title="Mean Forward Return",
        yaxis_tickformat='.2%',
        height=400,
        template='plotly_white',
        showlegend=False
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return fig
