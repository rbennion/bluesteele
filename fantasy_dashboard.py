#!/usr/bin/env python3
"""
Fantasy Football Auction Analysis Dashboard

Interactive Streamlit dashboard for analyzing fantasy football auction data
across multiple years with positional tier analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import numpy as np
import os
import subprocess
import sys
import base64
import re
from typing import Dict, List, Tuple

# App version
VERSION = "1.3"


# Page configuration
st.set_page_config(
    page_title="Blue Steele Fantasy Analysis",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App style overrides
st.markdown("""
<style>
    .main .block-container {
        max-width: 100%;
        padding-top: 5rem !important;
        padding-bottom: 0rem;
    }
    .block-container {
        padding-top: 5rem !important;
    }
    /* Keep dashboard always on top styling */
    .stApp {
        background-color: #f0f2f6;
    }
    /* Minimal padding adjustments */
    /* Remove top padding from main container */
    .main > div:first-child {
        padding-top: 0rem !important;
    }
    /* Keep streamlit header and toolbar visible */
    /* Remove extra space above tabs */
    .stTabs [data-baseweb="tab-list"] {
        margin-top: 0 !important;
    }
    /* Hide duplicate separators */
    hr:first-of-type {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        margin-top: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    /* Header styling for GIF layout */
    .stColumn > div {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 0;
    }
    /* Remove extra spacing from columns */
    .stColumn {
        padding: 0 !important;
    }
    /* Compact header layout */
    .header-container {
        margin-bottom: 0.5rem;
        padding: 0;
    }
    /* Blue Steel theme */
    .blue-steel-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_gif_as_base64(gif_path: str) -> str:
    """Load GIF file and convert to base64 for HTML embedding."""
    try:
        import base64
        with open(gif_path, "rb") as gif_file:
            return base64.b64encode(gif_file.read()).decode()
    except FileNotFoundError:
        return ""

def ensure_database_exists():
    """Ensure the database exists. For Cloud we ship the DB in Git."""
    # No creation here; app.py handles creation for local, and Cloud uses committed DB
    return

def load_data():
    """Load data from SQLite database."""
    # Ensure database exists first
    ensure_database_exists()
    
    try:
        conn = sqlite3.connect('fantasy_auction.db')
        
        # Load main data
        query = """
        SELECT 
            position,
            position_rank,
            year,
            auction_value / 100.0 as auction_value_dollars,
            position || position_rank as tier_label
        FROM auction_data
        ORDER BY year, position, position_rank
        """
        df = pd.read_sql_query(query, conn)
        
        # Load summary stats
        summary_query = """
        SELECT 
            position,
            position_rank,
            tier_label,
            COUNT(*) as years_of_data,
            ROUND(MIN(auction_value_dollars), 2) as min_price,
            ROUND(AVG(auction_value_dollars), 2) as avg_price,
            ROUND(MAX(auction_value_dollars), 2) as max_price
        FROM position_tiers
        WHERE position_rank <= 15
        GROUP BY position, position_rank
        ORDER BY position, position_rank
        """
        summary_df = pd.read_sql_query(summary_query, conn)
        
        conn.close()
        return df, summary_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()


def create_position_trend_chart(df: pd.DataFrame, positions: List[str], max_rank: int = 5):
    """Create clean line chart showing position tier trends over time."""
    filtered_df = df[
        (df['position'].isin(positions)) & 
        (df['position_rank'] <= max_rank)
    ]
    
    # Create a cleaner chart focusing on tier 1 players by default, with option to show more
    if max_rank <= 3:
        # Show fewer lines for clarity
        display_df = filtered_df
        title = f'Top {max_rank} Tier{"s" if max_rank > 1 else ""} by Position'
    else:
        # For larger datasets, focus on tier 1 players primarily
        tier1_df = filtered_df[filtered_df['position_rank'] == 1].copy()
        tier1_df['display_label'] = tier1_df['position'] + '1'
        
        # Add tier 2 for comparison but with different styling
        tier2_df = filtered_df[filtered_df['position_rank'] == 2].copy()
        tier2_df['display_label'] = tier2_df['position'] + '2'
        
        display_df = pd.concat([tier1_df, tier2_df])
        title = 'Position Tier 1 vs Tier 2 Comparison'
    
    # Custom color scheme - distinct colors for each position
    color_map = {
        'QB1': '#1f77b4', 'QB2': '#aec7e8',  # Blues
        'RB1': '#ff7f0e', 'RB2': '#ffbb78',  # Oranges  
        'WR1': '#2ca02c', 'WR2': '#98df8a',  # Greens
        'TE1': '#d62728', 'TE2': '#ff9896',  # Reds
        'Def1': '#9467bd', 'Def2': '#c5b0d5', # Purples
        'TMPK1': '#8c564b', 'TMPK2': '#c49c94' # Browns
    }
    
    if max_rank <= 3:
        fig = px.line(
            display_df,
            x='year',
            y='auction_value_dollars',
            color='tier_label',
            title=title,
            labels={
                'auction_value_dollars': 'Auction Value ($)',
                'year': 'Year',
                'tier_label': 'Position Tier'
            },
            height=500
        )
    else:
        fig = px.line(
            display_df,
            x='year',
            y='auction_value_dollars',
            color='display_label',
            line_dash='position_rank',
            title=title,
            labels={
                'auction_value_dollars': 'Auction Value ($)',
                'year': 'Year',
                'display_label': 'Position Tier'
            },
            height=500
        )
    
    # Update styling for clarity
    fig.update_traces(
        mode='lines+markers', 
        line=dict(width=3), 
        marker=dict(size=6)
    )
    
    fig.update_layout(
        xaxis=dict(
            tickmode='linear', 
            dtick=1,
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            tickformat='$,.0f',
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        title=dict(
            font=dict(size=16),
            x=0.5,
            xanchor='center'
        ),
        hovermode='x unified',
        legend=dict(
            orientation="v", 
            yanchor="top", 
            y=1, 
            xanchor="left", 
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add grid for better readability
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig


def create_tier_comparison_chart(df: pd.DataFrame, position: str, year: int):
    """Create bar chart comparing tiers within a position for a specific year."""
    filtered_df = df[
        (df['position'] == position) & 
        (df['year'] == year) & 
        (df['position_rank'] <= 12)
    ]
    
    fig = px.bar(
        filtered_df,
        x='tier_label',
        y='auction_value_dollars',
        title=f'{position} Position Tiers - {year}',
        labels={
            'auction_value_dollars': 'Auction Value ($)',
            'tier_label': f'{position} Tier'
        },
        color='auction_value_dollars',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        yaxis=dict(tickformat='$,.0f'),
        showlegend=False,
        height=400
    )
    
    return fig


def create_position_comparison_heatmap(df: pd.DataFrame, years: List[int]):
    """Create heatmap comparing top tiers across positions and years."""
    # Filter for top 5 of each position for better visualization
    filtered_df = df[
        (df['year'].isin(years)) & 
        (df['position_rank'] <= 5) &
        (df['position'].isin(['QB', 'RB', 'WR', 'TE']))
    ]
    
    if filtered_df.empty:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title='Position Tier Auction Values Across Years',
            height=400
        )
        return fig
    
    # Create a more flexible heatmap by position and tier
    # Instead of using years as columns, use position tiers
    pivot_df = filtered_df.pivot_table(
        values='auction_value_dollars',
        index='position',
        columns='position_rank',
        aggfunc='mean'
    )
    
    # Ensure we have data
    if pivot_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for heatmap visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title='Position Tier Auction Values Across Years',
            height=400
        )
        return fig
    
    # Create the heatmap
    fig = px.imshow(
        pivot_df.values,
        x=[f"Tier {i}" for i in pivot_df.columns],
        y=pivot_df.index,
        color_continuous_scale='Blues',
        title=f'Average Position Tier Values ({min(years)}-{max(years)})',
        labels=dict(color="Auction Value ($)", x="Position Tier", y="Position"),
        aspect="auto"
    )
    
    # Add text annotations
    for i, position in enumerate(pivot_df.index):
        for j, tier in enumerate(pivot_df.columns):
            value = pivot_df.iloc[i, j]
            if not pd.isna(value):
                fig.add_annotation(
                    x=j, y=i,
                    text=f"${value:.0f}",
                    showarrow=False,
                    font=dict(
                        color="white" if value > pivot_df.values.mean() else "darkblue",
                        size=12,
                        weight="bold"
                    )
                )
    
    fig.update_layout(
        height=500,
        xaxis_title="Position Tier",
        yaxis_title="Position"
    )
    return fig


def create_value_dropoff_chart(df: pd.DataFrame, position: str):
    """Create chart showing value dropoff between tiers."""
    position_df = df[
        (df['position'] == position) & 
        (df['position_rank'] <= 10)
    ].groupby(['year', 'position_rank'])['auction_value_dollars'].mean().reset_index()
    
    # Calculate average dropoff
    avg_by_rank = position_df.groupby('position_rank')['auction_value_dollars'].mean().reset_index()
    avg_by_rank['dropoff'] = avg_by_rank['auction_value_dollars'].diff() * -1
    avg_by_rank['dropoff_pct'] = (avg_by_rank['dropoff'] / avg_by_rank['auction_value_dollars'].shift(1)) * 100
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Average Auction Value by Tier', 'Value Dropoff Between Tiers'],
        vertical_spacing=0.15
    )
    
    # Top chart: Average values
    fig.add_trace(
        go.Bar(
            x=[f"{position}{r}" for r in avg_by_rank['position_rank']],
            y=avg_by_rank['auction_value_dollars'],
            name='Avg Value',
            marker_color='lightblue'
        ),
        row=1, col=1
    )
    
    # Bottom chart: Dropoffs
    fig.add_trace(
        go.Bar(
            x=[f"{position}{r}" for r in avg_by_rank['position_rank'][1:]],
            y=avg_by_rank['dropoff'][1:],
            name='$ Dropoff',
            marker_color='coral'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f'{position} Position Value Analysis',
        height=600,
        showlegend=False
    )
    
    fig.update_yaxes(title_text="Auction Value ($)", tickformat='$,.0f', row=1, col=1)
    fig.update_yaxes(title_text="Dropoff ($)", tickformat='$,.0f', row=2, col=1)
    
    return fig


def create_volatility_analysis(df: pd.DataFrame):
    """Create chart showing price volatility by position tier."""
    # Calculate coefficient of variation for each tier
    volatility_data = []
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        for rank in range(1, 6):
            tier_data = df[
                (df['position'] == position) & 
                (df['position_rank'] == rank)
            ]['auction_value_dollars']
            
            if len(tier_data) > 1:
                mean_val = tier_data.mean()
                std_val = tier_data.std()
                cv = (std_val / mean_val) * 100 if mean_val > 0 else 0
                
                volatility_data.append({
                    'tier_label': f"{position}{rank}",
                    'position': position,
                    'rank': rank,
                    'mean_value': mean_val,
                    'std_dev': std_val,
                    'coefficient_of_variation': cv
                })
    
    volatility_df = pd.DataFrame(volatility_data)
    
    if volatility_df.empty:
        # Return empty figure if no data
        fig = px.scatter(title='Position Tier Volatility Analysis - No Data Available')
        fig.add_annotation(
            text="No sufficient data for volatility analysis<br>Need multiple years of data per tier",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font_size=16
        )
        return fig
    
    fig = px.scatter(
        volatility_df,
        x='mean_value',
        y='coefficient_of_variation',
        color='position',
        size='rank',
        hover_data=['tier_label'],
        title='Position Tier Volatility Analysis',
        labels={
            'mean_value': 'Average Auction Value ($)',
            'coefficient_of_variation': 'Coefficient of Variation (%)',
            'position': 'Position'
        }
    )
    
    fig.update_layout(
        xaxis=dict(tickformat='$,.0f'),
        height=500
    )
    
    return fig


def main():
    """Main dashboard function."""
    
    # Header with Blue Steel GIF
    gif_base64 = load_gif_as_base64("image-asset.gif")
    
    # Create compact header layout
    if gif_base64:
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin: 0; padding: 0;">
            <img src="data:image/gif;base64,{gif_base64}" width="120" style="border-radius: 10px;">
            <h1 style="color: #1f77b4; font-size: 3rem; margin: 0; text-align: center;">💙 Blue Steele Fantasy Analysis</h1>
            <img src="data:image/gif;base64,{gif_base64}" width="120" style="border-radius: 10px;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<h1 class="main-header">💙 Blue Steele Fantasy Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading auction data..."):
        df, summary_df = load_data()
    
    if df.empty:
        st.error("No data available. Please ensure the database file exists.")
        return
    
    # In-page controls (top control bar)
    years = sorted(df['year'].unique())
    if 'selected_years' not in st.session_state:
        st.session_state.selected_years = years[-5:] if len(years) >= 5 else years

    positions = sorted(df['position'].unique())

    st.markdown("### 📊 Controls")
    c_years, c_positions, c_tiers = st.columns([1.2, 1.2, 1.6])

    # Years selector
    with c_years:
        selected_years = st.multiselect(
            "Years",
            options=years,
            key="selected_years",
            help="Choose any years to include"
        )

    if not selected_years:
        st.info("Select at least one year to view results.")
        return

    # Positions selector
    with c_positions:
        selected_positions = st.multiselect(
            "Positions",
            options=positions,
            default=positions,
            key="selected_positions"
        )

    # Build available tier numbers (position_rank) based on selected years and positions
    filtered_for_controls = df[
        (df['year'].isin(selected_years)) &
        (df['position'].isin(selected_positions))
    ]
    available_ranks = sorted(filtered_for_controls['position_rank'].dropna().unique().tolist())
    # Cap the number of tiers shown to a reasonable maximum
    TIER_CAP = 15
    available_ranks = [r for r in available_ranks if r <= TIER_CAP]
    if not available_ranks:
        available_ranks = list(range(1, TIER_CAP + 1))

    # Tier selector (single dropdown)
    with c_tiers:
        if available_ranks:
            selected_rank = st.selectbox(
                "Max Displayed Tiers",
                options=available_ranks,
                index=0,
                key="selected_tier",
                help="Choose a tier number"
            )
        else:
            selected_rank = None

    if not selected_positions or selected_rank is None:
        st.info("Select at least one position and tier to view results.")
        return

    st.caption(f"Analyzing: {min(selected_years)}–{max(selected_years)} ({len(selected_years)} years)")

    # Filter by selected years, positions, and tiers
    year_filtered_df = df[
        (df['year'].isin(selected_years)) &
        (df['position'].isin(selected_positions)) &
        (df['position_rank'] <= selected_rank)
    ]

    st.markdown("---")

    # Single-screen: Tier Prices
    st.header("Tier Prices")

    if year_filtered_df.empty:
        st.warning("No data available for selected filters.")
    else:
        view_df = year_filtered_df

        # Summary table
        st.subheader(f"Summary ({min(selected_years)}-{max(selected_years)})")
        summary = (
            view_df.groupby('tier_label')['auction_value_dollars']
            .agg(mean='mean', min='min', max='max', years='count')
            .reset_index()
        )
        # Natural sort tiers like QB1, QB2, ..., QB10 correctly
        def parse_tier(tier_label: str) -> tuple:
            match = re.match(r"^([A-Za-z]+)(\d+)$", tier_label)
            if match:
                return (match.group(1), int(match.group(2)))
            return (tier_label, 0)

        summary = summary.sort_values(by='tier_label', key=lambda s: s.map(parse_tier))

        summary_display = summary.copy()
        summary_display['Average ($)'] = summary_display['mean'].round(0).map(lambda x: f"${x:,.0f}")
        summary_display['Min ($)'] = summary_display['min'].round(0).map(lambda x: f"${x:,.0f}")
        summary_display['Max ($)'] = summary_display['max'].round(0).map(lambda x: f"${x:,.0f}")
        summary_display = summary_display[['tier_label', 'Average ($)', 'Min ($)', 'Max ($)', 'years']]
        summary_display.columns = ['Tier', 'Average ($)', 'Min ($)', 'Max ($)', 'Years']
        st.dataframe(summary_display, use_container_width=True, hide_index=True)

        # Averages bar chart
        st.subheader("Average by Tier")
        chart_df = summary[['tier_label', 'mean']].copy()
        fig = px.bar(
            chart_df,
            x='tier_label',
            y='mean',
            labels={'tier_label': 'Tier', 'mean': 'Average ($)'},
            color='mean',
            color_continuous_scale='Blues',
            height=420
        )
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickformat='$,.0f')
        st.plotly_chart(fig, use_container_width=True)

        # Year-by-year table
        st.subheader("Year-by-Year (Average if multiple)")
        yby = (
            view_df.pivot_table(index='year', columns='tier_label', values='auction_value_dollars', aggfunc='mean')
            .loc[selected_years]
            .round(2)
        )
        st.dataframe(yby, use_container_width=True)
    
    # Footer
    st.markdown("---")
    # Compute footer metadata
    latest_year = int(df['year'].max()) if not df.empty else 'N/A'
    # Get file modified date for DB or CSV
    data_file = os.path.join(os.path.dirname(__file__), 'fantasy_auction.db')
    if not os.path.exists(data_file):
        data_file = os.path.join(os.path.dirname(__file__), 'data', 'WSOFF through 2024 Raw Data.csv')
    last_updated = ''
    if os.path.exists(data_file):
        try:
            ts = os.path.getmtime(data_file)
            from datetime import datetime
            last_updated = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        except Exception:
            last_updated = 'N/A'
    else:
        last_updated = 'N/A'

    st.markdown(
        "**Blue Steele Fantasy Analysis** | "
        f"**Data Through:** {latest_year} | "
        f"**Last Updated:** {last_updated} | "
        f"**Version:** {VERSION}"
    )


if __name__ == "__main__":
    main()
