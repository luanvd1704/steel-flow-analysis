"""
Common visualization utilities
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import COLOR_PALETTE, QUINTILE_COLORS, CHART_HEIGHT, CHART_WIDTH


def create_bar_chart(data: pd.DataFrame,
                     x_col: str,
                     y_col: str,
                     title: str,
                     x_label: str = None,
                     y_label: str = None,
                     color_col: str = None,
                     colors: List[str] = None) -> go.Figure:
    """
    Create a bar chart

    Args:
        data: DataFrame
        x_col: X-axis column
        y_col: Y-axis column
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        color_col: Column for coloring
        colors: Custom colors

    Returns:
        Plotly figure
    """
    if colors is None and color_col is None:
        colors = [COLOR_PALETTE['primary']] * len(data)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data[x_col],
        y=data[y_col],
        marker_color=colors if colors else None,
        marker=dict(color=data[color_col]) if color_col else None
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label or x_col,
        yaxis_title=y_label or y_col,
        height=CHART_HEIGHT,
        template='plotly_white'
    )

    return fig


def create_heatmap(data: pd.DataFrame,
                   title: str,
                   x_label: str = None,
                   y_label: str = None,
                   colorscale: str = 'RdYlGn') -> go.Figure:
    """
    Create a heatmap

    Args:
        data: DataFrame (will be used as matrix)
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        colorscale: Color scale

    Returns:
        Plotly figure
    """
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale=colorscale,
        text=data.values,
        texttemplate='%{text:.3f}',
        textfont={"size": 10}
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=CHART_HEIGHT
    )

    return fig


def create_line_chart(data: pd.DataFrame,
                     x_col: str,
                     y_cols: List[str],
                     title: str,
                     x_label: str = None,
                     y_label: str = None,
                     legend_labels: List[str] = None) -> go.Figure:
    """
    Create a line chart

    Args:
        data: DataFrame
        x_col: X-axis column
        y_cols: List of Y-axis columns
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        legend_labels: Custom legend labels

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    for i, y_col in enumerate(y_cols):
        label = legend_labels[i] if legend_labels else y_col

        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode='lines+markers',
            name=label
        ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label or x_col,
        yaxis_title=y_label,
        height=CHART_HEIGHT,
        template='plotly_white'
    )

    return fig


def add_significance_markers(fig: go.Figure,
                            x_values: List,
                            y_values: List,
                            p_values: List,
                            threshold: float = 0.05) -> go.Figure:
    """
    Add significance markers (* for p < 0.05) to chart

    Args:
        fig: Plotly figure
        x_values: X positions for markers
        y_values: Y positions for markers
        p_values: P-values
        threshold: Significance threshold

    Returns:
        Updated figure
    """
    for x, y, p in zip(x_values, y_values, p_values):
        if p < threshold:
            fig.add_annotation(
                x=x,
                y=y,
                text="*",
                showarrow=False,
                font=dict(size=20, color='red'),
                yshift=10
            )

    return fig


def format_percentage_axis(fig: go.Figure, axis: str = 'y') -> go.Figure:
    """
    Format axis as percentage

    Args:
        fig: Plotly figure
        axis: 'x' or 'y'

    Returns:
        Updated figure
    """
    if axis == 'y':
        fig.update_yaxes(tickformat='.2%')
    else:
        fig.update_xaxes(tickformat='.2%')

    return fig
