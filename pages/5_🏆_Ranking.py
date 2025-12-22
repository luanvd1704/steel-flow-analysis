"""
Banking Ranking Page - 4 Biểu Đồ Phân Tích
Composite Score + 3 Scatter Charts
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config_banking
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Ranking", page_icon="🏆", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

# ==============================================================================
# DATA LOADING
# ==============================================================================

@st.cache_data
def load_banking_metrics():
    """Load banking_metrics.csv"""
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'banking_metrics.csv')
    df = pd.read_csv(csv_path)
    return df

# ==============================================================================
# COMPOSITE SCORE CALCULATION
# ==============================================================================

def calculate_composite_score(df):
    """
    Calculate composite score (0-100) using percentile normalization

    Steps:
    1. Cap OCF/NP at 3
    2. Normalize using percentile rank (0-100)
    3. Apply weights
    4. Calculate final score
    """
    result = df.copy()

    # Step 1: Cap OCF/NP
    result['OCF_cap'] = result['OCF_to_NP_TTM'].clip(upper=3)

    # Step 2: Percentile normalization (0-100)
    # Higher is better
    result['ROA_S'] = result['ROA'].rank(pct=True, method='average') * 100
    result['NetProfit_YoY_S'] = result['NetProfit_YoY'].rank(pct=True, method='average') * 100
    result['OperatingIncome_YoY_S'] = result['OperatingIncome_YoY'].rank(pct=True, method='average') * 100
    result['Equity_to_Assets_S'] = result['Equity_to_Assets'].rank(pct=True, method='average') * 100
    result['OCF_S'] = result['OCF_cap'].rank(pct=True, method='average') * 100

    # Lower is better (inverted)
    result['CIR_S'] = (1 - result['CIR_TTM'].rank(pct=True, method='average')) * 100
    result['LDR_S'] = (1 - result['LDR'].rank(pct=True, method='average')) * 100

    # Step 3: Weighted score
    result['Score'] = (
        0.20 * result['ROA_S'] +
        0.20 * result['NetProfit_YoY_S'] +
        0.08 * result['OperatingIncome_YoY_S'] +
        0.18 * result['CIR_S'] +
        0.15 * result['Equity_to_Assets_S'] +
        0.12 * result['LDR_S'] +
        0.07 * result['OCF_S']
    )

    # Step 4: Ranking
    result = result.sort_values('Score', ascending=False).reset_index(drop=True)
    result['Rank'] = range(1, len(result) + 1)

    return result

# ==============================================================================
# PROFILE CLASSIFICATION
# ==============================================================================

def classify_profile(row):
    """
    Classify bank profile (max 2 labels)
    Priority: Hiệu quả > An toàn > Tăng trưởng
    """
    labels = []

    # Hiệu quả (highest priority)
    if row['ROA'] >= 1.7 and row['CIR_TTM'] <= 30:
        labels.append('Hiệu quả')

    # An toàn
    if row['Equity_to_Assets'] >= 10 and row['LDR'] <= 115:
        labels.append('An toàn')

    # Tăng trưởng
    if row['NetProfit_YoY'] >= 20 or row['OperatingIncome_YoY'] >= 15:
        labels.append('Tăng trưởng')

    # Return max 2 labels
    if len(labels) == 0:
        return 'Trung tính'
    elif len(labels) <= 2:
        return ', '.join(labels)
    else:
        return ', '.join(labels[:2])

def get_profile_color(profile):
    """Map profile to bar color"""
    if 'Hiệu quả' in profile:
        return '#28a745'  # Green
    elif 'An toàn' in profile:
        return '#007bff'  # Blue
    elif 'Tăng trưởng' in profile:
        return '#fd7e14'  # Orange
    else:
        return '#6c757d'  # Gray

# ==============================================================================
# RISK FLAGS
# ==============================================================================

def get_risk_flags(row):
    """Generate risk flags"""
    flags = []

    if row['LDR'] > 140:
        flags.append('LDR rất cao')
    elif row['LDR'] > 125:
        flags.append('LDR cao')

    if row['CIR_TTM'] > 40:
        flags.append('CIR cao')

    if row['NetProfit_YoY'] < 0 or row['OperatingIncome_YoY'] < 0:
        flags.append('Tăng trưởng âm')

    if row['OCF_to_NP_TTM'] < 1:
        flags.append('OCF/NP < 1')

    return ', '.join(flags) if flags else '—'

# ==============================================================================
# TABLE STYLING
# ==============================================================================

def style_ranking_table(styled_df):
    """Apply color highlighting to ranking table"""

    def highlight_flags(val):
        """Red background for cells with flags"""
        if val != '—':
            return 'background-color: #fff5f5; color: #000000; font-weight: 500'
        return ''

    def highlight_ldr(val):
        """Color LDR based on thresholds"""
        if val > 140:
            return 'background-color: #fff0f0; color: #000000; font-weight: 500'  # Red
        elif val > 125:
            return 'background-color: #fff8f0; color: #000000; font-weight: 500'  # Orange
        elif val <= 115:
            return 'background-color: #f0fff0; color: #000000; font-weight: 500'  # Green
        return ''

    def highlight_cir(val):
        """Color CIR based on thresholds"""
        if val > 40:
            return 'background-color: #fff0f0; color: #000000; font-weight: 500'  # Red
        elif val <= 30:
            return 'background-color: #f0fff0; color: #000000; font-weight: 500'  # Green
        return ''

    def highlight_ocf(val):
        """Color OCF/NP based on thresholds"""
        if val < 1:
            return 'background-color: #fff0f0; color: #000000; font-weight: 500'  # Red
        elif val > 3:
            return 'background-color: #f0fff0; color: #000000; font-weight: 500'  # Green
        return ''

    def highlight_growth(val):
        """Color growth metrics"""
        if val < 0:
            return 'background-color: #fff0f0; color: #000000; font-weight: 500'  # Red
        elif val > 20:
            return 'background-color: #f0fff0; color: #000000; font-weight: 500'  # Green
        return ''

    def highlight_profile(val):
        """Color text for Profile column"""
        if 'Hiệu quả' in str(val):
            return 'color: #28a745; font-weight: bold'
        elif 'An toàn' in str(val):
            return 'color: #007bff; font-weight: bold'
        elif 'Tăng trưởng' in str(val):
            return 'color: #fd7e14; font-weight: bold'
        return 'color: #6c757d'

    # Apply styling
    styled_df = styled_df.map(highlight_flags, subset=['Flags'])
    styled_df = styled_df.map(highlight_ldr, subset=['LDR'])
    styled_df = styled_df.map(highlight_cir, subset=['CIR_TTM'])
    styled_df = styled_df.map(highlight_ocf, subset=['OCF_to_NP_TTM'])
    styled_df = styled_df.map(highlight_growth, subset=['NetProfit_YoY', 'OperatingIncome_YoY'])
    styled_df = styled_df.map(highlight_profile, subset=['Profile'])

    return styled_df

# ==============================================================================
# CHART 1: COMPOSITE SCORE BAR CHART
# ==============================================================================

def plot_composite_score(df):
    """
    Bar chart: Overall Score (0-100)
    - X: Ticker (sorted by Score desc)
    - Y: Score
    - Color: By Profile
    - Annotation: "!" if has flags
    """
    fig = go.Figure()

    for idx, row in df.iterrows():
        color = get_profile_color(row['Profile'])

        # Bar
        fig.add_trace(go.Bar(
            x=[row['Ticker']],
            y=[row['Score']],
            name=row['Ticker'],
            marker_color=color,
            hovertemplate=(
                f"<b>{row['Ticker']}</b><br>"
                f"Score: {row['Score']:.1f}<br>"
                f"Rank: {row['Rank']}<br>"
                f"Profile: {row['Profile']}<br>"
                f"Flags: {row['Flags']}<br>"
                f"<br><b>Raw Metrics:</b><br>"
                f"ROA: {row['ROA']:.2f}%<br>"
                f"NetProfit YoY: {row['NetProfit_YoY']:.2f}%<br>"
                f"OperatingIncome YoY: {row['OperatingIncome_YoY']:.2f}%<br>"
                f"CIR: {row['CIR_TTM']:.2f}%<br>"
                f"Equity/Assets: {row['Equity_to_Assets']:.2f}%<br>"
                f"LDR: {row['LDR']:.2f}%<br>"
                f"OCF/NP: {row['OCF_to_NP_TTM']:.2f}<br>"
                "<extra></extra>"
            ),
            showlegend=False
        ))

        # Add "!" annotation if has flags
        if row['Flags'] != '—':
            fig.add_annotation(
                x=row['Ticker'],
                y=row['Score'],
                text="!",
                showarrow=False,
                font=dict(size=18, color='red', family='Arial Black'),
                yshift=15
            )

    fig.update_layout(
        title="📊 Xếp Hạng Tổng Hợp (Composite Score)",
        xaxis_title="Ngân Hàng",
        yaxis_title="Score (0-100)",
        yaxis=dict(range=[0, 105]),
        height=500,
        showlegend=False,
        hovermode='closest'
    )

    return fig

# ==============================================================================
# CHART 2: CIR VS ROA SCATTER
# ==============================================================================

def plot_efficiency_scatter(df):
    """
    Scatter: CIR (X) vs ROA (Y)
    Quadrant: Top-left = Best (low CIR, high ROA)
    """
    fig = px.scatter(
        df,
        x='CIR_TTM',
        y='ROA',
        text='Ticker',
        title="💼 Hiệu Quả Vận Hành: CIR vs ROA",
        labels={
            'CIR_TTM': 'CIR (%) - Thấp hơn = Tốt hơn',
            'ROA': 'ROA (%) - Cao hơn = Tốt hơn'
        },
        hover_data={
            'Ticker': True,
            'CIR_TTM': ':.2f',
            'ROA': ':.2f',
            'Score': ':.1f',
            'Rank': True
        }
    )

    fig.update_traces(
        textposition='top center',
        marker=dict(size=12, color='#007bff')
    )

    fig.update_layout(height=400)

    return fig

# ==============================================================================
# CHART 3: LDR VS NETPROFIT_YOY SCATTER
# ==============================================================================

def plot_growth_risk_scatter(df):
    """
    Scatter: LDR (X) vs NetProfit_YoY (Y)
    Insight: High LDR + High Growth = Liquidity risk
    """
    fig = px.scatter(
        df,
        x='LDR',
        y='NetProfit_YoY',
        text='Ticker',
        title="⚠️ Tăng Trưởng vs Rủi Ro Thanh Khoản: LDR vs NetProfit YoY",
        labels={
            'LDR': 'LDR (%) - Cao = Rủi ro thanh khoản',
            'NetProfit_YoY': 'Net Profit YoY (%)'
        },
        hover_data={
            'Ticker': True,
            'LDR': ':.2f',
            'NetProfit_YoY': ':.2f',
            'Score': ':.1f',
            'Rank': True
        }
    )

    # Add reference line at LDR = 115
    fig.add_vline(x=115, line_dash="dash", line_color="red",
                  annotation_text="LDR = 115 (Ngưỡng an toàn)")

    fig.update_traces(
        textposition='top center',
        marker=dict(size=12, color='#fd7e14')
    )

    fig.update_layout(height=400)

    return fig

# ==============================================================================
# CHART 4: OCF/NP VS NETPROFIT_YOY SCATTER
# ==============================================================================

def plot_profit_quality_scatter(df):
    """
    Scatter: OCF_to_NP_TTM (X) vs NetProfit_YoY (Y)
    Quadrant: Top-right = Best (high OCF/NP, high growth)
    """
    fig = px.scatter(
        df,
        x='OCF_to_NP_TTM',
        y='NetProfit_YoY',
        text='Ticker',
        title="💰 Chất Lượng Lợi Nhuận: OCF/NP vs NetProfit YoY",
        labels={
            'OCF_to_NP_TTM': 'OCF/Net Profit (TTM) - Cao = Dòng tiền tốt',
            'NetProfit_YoY': 'Net Profit YoY (%)'
        },
        hover_data={
            'Ticker': True,
            'OCF_to_NP_TTM': ':.2f',
            'NetProfit_YoY': ':.2f',
            'Score': ':.1f',
            'Rank': True
        }
    )

    # Add reference line at OCF/NP = 1
    fig.add_vline(x=1, line_dash="dash", line_color="red",
                  annotation_text="OCF/NP = 1")

    fig.update_traces(
        textposition='top center',
        marker=dict(size=12, color='#28a745')
    )

    fig.update_layout(height=500)

    return fig

# ==============================================================================
# MAIN PAGE
# ==============================================================================

st.title("🏆 Xếp Hạng Ngân Hàng")
st.markdown("Phân tích tổng hợp dựa trên 7 chỉ số tài chính (Q3/2025)")

# Load data
df = load_banking_metrics()

# Calculate composite score
df = calculate_composite_score(df)
df['Profile'] = df.apply(classify_profile, axis=1)
df['Flags'] = df.apply(get_risk_flags, axis=1)

# Chart 1: Composite Score (Full Width)
st.plotly_chart(plot_composite_score(df), use_container_width=True)

# Ranking Table
st.subheader("📋 Bảng Xếp Hạng Chi Tiết")
display_cols = ['Rank', 'Ticker', 'Score', 'Profile', 'Flags',
                'ROA', 'NetProfit_YoY', 'OperatingIncome_YoY', 'CIR_TTM',
                'Equity_to_Assets', 'LDR', 'OCF_to_NP_TTM']
styled_table = df[display_cols].style.format({
    'Score': '{:.1f}',
    'ROA': '{:.2f}',
    'NetProfit_YoY': '{:.2f}',
    'OperatingIncome_YoY': '{:.2f}',
    'CIR_TTM': '{:.2f}',
    'Equity_to_Assets': '{:.2f}',
    'LDR': '{:.2f}',
    'OCF_to_NP_TTM': '{:.2f}'
})

# Apply color styling
styled_table = style_ranking_table(styled_table)

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)

# Charts 2 & 3 (Vertical)
st.plotly_chart(plot_efficiency_scatter(df), use_container_width=True)
st.plotly_chart(plot_growth_risk_scatter(df), use_container_width=True)

# Chart 4: Profit Quality (Full Width)
st.plotly_chart(plot_profit_quality_scatter(df), use_container_width=True)

# Footer
st.markdown("---")
st.caption("""
**Ghi chú:**
- **Score (0-100)**: Weighted combination của 7 metrics (ROA: 20%, NetProfit YoY: 20%, CIR: 18%, Equity: 15%, LDR: 12%, OpIncome YoY: 8%, OCF: 7%)
- **Profile**:
  - Hiệu quả (ROA ≥ 1.7%, CIR ≤ 30%)
  - An toàn (Equity/Assets ≥ 10%, LDR ≤ 115%)
  - Tăng trưởng (NetProfit YoY ≥ 20% OR OpIncome YoY ≥ 15%)
- **Flags**: Cảnh báo rủi ro (LDR > 125%, CIR > 40%, Growth < 0%, OCF/NP < 1)
- **Normalization**: Percentile rank (0-100) với OCF/NP capped tại 3
""")
