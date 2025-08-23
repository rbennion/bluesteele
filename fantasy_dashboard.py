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
from typing import Dict, List, Tuple


# Page configuration
st.set_page_config(
    page_title="Blue Steele Fantasy Analysis",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh configuration to keep dashboard always visible
st.markdown("""
<meta http-equiv="refresh" content="300">
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
    /* Remove default streamlit padding */
    .css-1d391kg {
        padding-top: 0rem;
    }
    .css-18e3th9 {
        padding-top: 0rem;
    }
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
    
    # Sidebar controls
    st.sidebar.header("📊 Dashboard Controls")
    
    # Year range selector with more options
    years = sorted(df['year'].unique())
    
    st.sidebar.subheader("📅 Year Selection")
    
    # Quick year presets
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Recent 3 Years", use_container_width=True):
            st.session_state.year_range = (max(years) - 2, max(years))
    with col2:
        if st.button("Recent 5 Years", use_container_width=True):
            st.session_state.year_range = (max(years) - 4, max(years))
    
    col3, col4 = st.sidebar.columns(2)
    with col3:
        if st.button("All Years", use_container_width=True):
            st.session_state.year_range = (min(years), max(years))
    with col4:
        if st.button("2020+", use_container_width=True):
            st.session_state.year_range = (2020, max(years))
    
    # Initialize session state if not exists
    if 'year_range' not in st.session_state:
        st.session_state.year_range = (min(years), max(years))
    
    # Year range slider
    year_range = st.sidebar.slider(
        "Custom Year Range",
        min_value=min(years),
        max_value=max(years),
        value=st.session_state.year_range,
        step=1,
        help="Drag to select custom year range for analysis"
    )
    
    # Update session state
    st.session_state.year_range = year_range
    
    # Show selected range prominently
    st.sidebar.info(f"**Analyzing:** {year_range[0]} - {year_range[1]} ({year_range[1] - year_range[0] + 1} years)")
    
    # Position selector
    positions = sorted(df['position'].unique())
    selected_positions = st.sidebar.multiselect(
        "Select Positions",
        positions,
        default=positions  # Show all positions by default
    )
    
    # Maximum tier selector
    max_tier = st.sidebar.slider(
        "Maximum Tier to Display",
        min_value=1,
        max_value=15,
        value=5,
        step=1
    )
    
    # Filter data based on selections
    filtered_df = df[
        (df['year'] >= year_range[0]) & 
        (df['year'] <= year_range[1]) &
        (df['position'].isin(selected_positions))
    ]
    
    st.markdown("---")
    
    # Main charts
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Trends Over Time", 
        "📊 Position Comparison", 
        "🔥 Tier Analysis", 
        "📉 Value Dropoffs",
        "⚡ Volatility Analysis",
        "⏱️ Period Comparison"
    ])
    
    with tab1:
        st.header("Position Tier Trends Over Time")
        
        if not filtered_df.empty:
            # Average values summary table - FIRST CHART
            st.subheader(f"📊 Average Auction Values ({year_range[0]}-{year_range[1]})")
            
            # Calculate averages for the selected time period
            avg_data = filtered_df[filtered_df['position_rank'] <= max_tier].groupby(
                ['position', 'position_rank']
            )['auction_value_dollars'].agg(['mean', 'min', 'max', 'count']).round(2)
            
            # Create a clean summary table - respects the max_tier slider
            summary_data = []
            for position in selected_positions:
                for rank in range(1, max_tier + 1):  # Use exactly the slider value
                    if (position, rank) in avg_data.index:
                        row_data = avg_data.loc[(position, rank)]
                        summary_data.append({
                            'Position Tier': f"{position}{rank}",
                            'Average ($)': f"${row_data['mean']:.0f}",
                            'Min ($)': f"${row_data['min']:.0f}",
                            'Max ($)': f"${row_data['max']:.0f}",
                            'Years': int(row_data['count'])
                        })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                
                # Display as an interactive table with highlighting
                st.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Position Tier": st.column_config.TextColumn("Position Tier", width="medium"),
                        "Average ($)": st.column_config.TextColumn("Average ($)", width="medium"),
                        "Min ($)": st.column_config.TextColumn("Min ($)", width="small"),
                        "Max ($)": st.column_config.TextColumn("Max ($)", width="small"),
                        "Years": st.column_config.NumberColumn("Years", width="small")
                    }
                )
                
                # Add some quick insights - find the actual highest value
                # Convert to numeric for proper sorting
                summary_df['avg_numeric'] = summary_df['Average ($)'].str.replace('$', '').str.replace(',', '').astype(float)
                highest_tier = summary_df.loc[summary_df['avg_numeric'].idxmax()]
                
                st.info(f"💡 **Quick Insight:** In your selected period, the highest average was {highest_tier['Position Tier']} at {highest_tier['Average ($)']} across {highest_tier['Years']} years.")
            
            st.markdown("---")
            
            # Create a much more useful bar chart showing averages
            st.subheader("📊 Average Values by Position Tier")
            
            # Calculate averages for bar chart
            chart_data = filtered_df[filtered_df['position_rank'] <= max_tier].groupby(
                'tier_label'
            )['auction_value_dollars'].mean().reset_index()
            
            # Sort by average value (highest first)
            chart_data = chart_data.sort_values('auction_value_dollars', ascending=False)
            
            # Create clean bar chart
            fig = px.bar(
                chart_data,
                x='tier_label',
                y='auction_value_dollars',
                title=f'Average Auction Values by Position Tier ({year_range[0]}-{year_range[1]})',
                labels={
                    'auction_value_dollars': 'Average Auction Value ($)',
                    'tier_label': 'Position Tier'
                },
                color='auction_value_dollars',
                color_continuous_scale='Blues',
                height=500
            )
            
            # Format the chart
            fig.update_layout(
                xaxis=dict(
                    title_font=dict(size=14),
                    tickfont=dict(size=12),
                    tickangle=45
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
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            # Add value labels on bars
            for i, row in chart_data.iterrows():
                fig.add_annotation(
                    x=row['tier_label'],
                    y=row['auction_value_dollars'],
                    text=f"${row['auction_value_dollars']:.0f}",
                    showarrow=False,
                    yshift=10,
                    font=dict(size=12, color='black')
                )
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **This chart shows the average auction value for each position tier over your selected time period. Higher bars = more expensive tiers.**")
            
            # Data table
            st.subheader("Detailed Trend Data")
            trend_data = filtered_df[filtered_df['position_rank'] <= max_tier].pivot_table(
                values='auction_value_dollars',
                index='tier_label',
                columns='year',
                aggfunc='mean'
            ).round(2)
            st.dataframe(trend_data, use_container_width=True)
        else:
            st.warning("No data available for selected filters.")
    
    with tab2:
        st.header("Position Comparison Analysis")
        
        if not filtered_df.empty:
            # Add visualization options
            viz_option = st.radio(
                "Choose visualization:",
                ["📊 Heatmap (Position vs Tiers)", "📈 Line Chart (Tiers Over Time)", "📋 Summary Table"],
                horizontal=True
            )
            
            if viz_option == "📊 Heatmap (Position vs Tiers)":
                selected_years = list(range(year_range[0], year_range[1] + 1))
                heatmap = create_position_comparison_heatmap(filtered_df, selected_years)
                st.plotly_chart(heatmap, use_container_width=True)
                
                st.info("This heatmap shows average auction values by position and tier for your selected time period. Darker colors = higher values.")
            
            elif viz_option == "📈 Line Chart (Tiers Over Time)":
                # Create line chart showing top tiers over time
                top_tiers_df = filtered_df[
                    (filtered_df['position_rank'] == 1) & 
                    (filtered_df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                ]
                
                if not top_tiers_df.empty:
                    fig = px.line(
                        top_tiers_df,
                        x='year',
                        y='auction_value_dollars',
                        color='position',
                        title='Top Tier (Rank 1) Position Values Over Time',
                        labels={
                            'auction_value_dollars': 'Auction Value ($)',
                            'year': 'Year',
                            'position': 'Position'
                        }
                    )
                    
                    fig.update_traces(mode='lines+markers', line=dict(width=3), marker=dict(size=8))
                    fig.update_layout(
                        yaxis=dict(tickformat='$,.0f'),
                        xaxis=dict(tickmode='linear', dtick=1),
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show tier comparison for each position
                    st.subheader("Position 1st vs 2nd vs 3rd Tier Comparison")
                    comparison_df = filtered_df[
                        (filtered_df['position_rank'] <= 3) &
                        (filtered_df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                    ]
                    
                    avg_by_tier = comparison_df.groupby(['position', 'position_rank'])['auction_value_dollars'].mean().reset_index()
                    
                    fig2 = px.bar(
                        avg_by_tier,
                        x='position',
                        y='auction_value_dollars',
                        color='position_rank',
                        title='Average Values: Top 3 Tiers by Position',
                        labels={
                            'auction_value_dollars': 'Average Auction Value ($)',
                            'position': 'Position',
                            'position_rank': 'Tier'
                        },
                        color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
                    )
                    
                    fig2.update_layout(
                        yaxis=dict(tickformat='$,.0f'),
                        height=400
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("No data available for line chart visualization.")
            
            else:  # Summary Table
                st.subheader("Position Tier Summary Statistics")
                comparison_data = filtered_df[filtered_df['position_rank'] <= 8].groupby(
                    ['position', 'position_rank']
                )['auction_value_dollars'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
                
                comparison_data.columns = ['Sample Size', 'Average ($)', 'Std Dev ($)', 'Min ($)', 'Max ($)']
                comparison_data = comparison_data.reset_index()
                comparison_data['Tier'] = comparison_data['position'] + comparison_data['position_rank'].astype(str)
                
                # Pivot for better display
                display_df = comparison_data.pivot(index='Tier', columns='position', values='Average ($)')
                st.dataframe(display_df, use_container_width=True)
                
                # Show detailed stats
                st.subheader("Detailed Statistics")
                st.dataframe(comparison_data[['Tier', 'Sample Size', 'Average ($)', 'Std Dev ($)', 'Min ($)', 'Max ($)']], use_container_width=True, hide_index=True)
        else:
            st.warning("No data available for selected filters.")
    
    with tab3:
        st.header("Individual Position Tier Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_position = st.selectbox(
                "Select Position for Analysis",
                selected_positions if selected_positions else positions
            )
        
        with col2:
            analysis_year = st.selectbox(
                "Select Year for Analysis",
                sorted(filtered_df['year'].unique(), reverse=True)
            )
        
        if analysis_position and analysis_year:
            tier_chart = create_tier_comparison_chart(filtered_df, analysis_position, analysis_year)
            st.plotly_chart(tier_chart, use_container_width=True)
            
            # Show tier data for selected position/year
            tier_data = filtered_df[
                (filtered_df['position'] == analysis_position) & 
                (filtered_df['year'] == analysis_year)
            ][['tier_label', 'auction_value_dollars']].sort_values('auction_value_dollars', ascending=False)
            
            st.subheader(f"{analysis_position} Tiers - {analysis_year}")
            st.dataframe(tier_data, use_container_width=True, hide_index=True)
    
    with tab4:
        st.header("Value Dropoff Analysis")
        
        dropoff_position = st.selectbox(
            "Select Position for Dropoff Analysis",
            selected_positions if selected_positions else positions,
            key="dropoff_position"
        )
        
        if dropoff_position:
            dropoff_chart = create_value_dropoff_chart(filtered_df, dropoff_position)
            st.plotly_chart(dropoff_chart, use_container_width=True)
            
            # Calculate and display dropoff statistics
            position_data = filtered_df[
                (filtered_df['position'] == dropoff_position) & 
                (filtered_df['position_rank'] <= 10)
            ].groupby('position_rank')['auction_value_dollars'].mean().reset_index()
            
            position_data['dropoff'] = position_data['auction_value_dollars'].diff() * -1
            position_data['dropoff_pct'] = (position_data['dropoff'] / position_data['auction_value_dollars'].shift(1)) * 100
            
            st.subheader(f"{dropoff_position} Dropoff Statistics")
            display_data = position_data[['position_rank', 'auction_value_dollars', 'dropoff', 'dropoff_pct']].copy()
            display_data.columns = ['Tier', 'Avg Value ($)', 'Dropoff ($)', 'Dropoff (%)']
            display_data = display_data.round(2)
            st.dataframe(display_data, use_container_width=True, hide_index=True)
    
    with tab5:
        st.header("Price Volatility Analysis")
        st.write("This chart shows how volatile each position tier's pricing has been over time.")
        
        volatility_chart = create_volatility_analysis(filtered_df)
        st.plotly_chart(volatility_chart, use_container_width=True)
        
        st.info("""
        **Interpretation:**
        - **X-axis**: Average auction value across all years
        - **Y-axis**: Coefficient of variation (higher = more volatile pricing)
        - **Bubble size**: Position tier (larger = lower tier)
        - **Color**: Position type
        
        Players in the top-right have high value AND high volatility (boom/bust).
        Players in the bottom-left have low value AND low volatility (consistent role players).
        """)
    
    with tab6:
        st.header("Period Comparison Analysis")
        st.write(f"Compare your selected period ({year_range[0]}-{year_range[1]}) with other periods")
        
        # Period comparison controls
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            st.subheader("🎯 Your Selected Period")
            st.write(f"**Years:** {year_range[0]} - {year_range[1]}")
            st.write(f"**Duration:** {year_range[1] - year_range[0] + 1} years")
            
            # Calculate averages for selected period
            selected_period_data = filtered_df[
                (filtered_df['position_rank'] <= 5) &
                (filtered_df['position'].isin(['QB', 'RB', 'WR', 'TE']))
            ].groupby(['position', 'tier_label'])['auction_value_dollars'].mean().reset_index()
            
            st.dataframe(
                selected_period_data.pivot(index='tier_label', columns='position', values='auction_value_dollars').round(2),
                use_container_width=True
            )
        
        with comp_col2:
            comparison_period = st.selectbox(
                "Compare with:",
                [
                    "All Other Years",
                    "Pre-2020 (2014-2019)", 
                    "Post-2020 (2020-2024)",
                    "Early Years (2014-2018)",
                    "Recent Years (2019-2024)"
                ]
            )
            
            # Calculate comparison data based on selection
            if comparison_period == "All Other Years":
                comp_data = df[
                    ~((df['year'] >= year_range[0]) & (df['year'] <= year_range[1])) &
                    (df['position_rank'] <= 5) &
                    (df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                ]
                comp_label = f"All years except {year_range[0]}-{year_range[1]}"
            elif comparison_period == "Pre-2020 (2014-2019)":
                comp_data = df[
                    (df['year'] < 2020) &
                    (df['position_rank'] <= 5) &
                    (df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                ]
                comp_label = "2014-2019"
            elif comparison_period == "Post-2020 (2020-2024)":
                comp_data = df[
                    (df['year'] >= 2020) &
                    (df['position_rank'] <= 5) &
                    (df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                ]
                comp_label = "2020-2024"
            elif comparison_period == "Early Years (2014-2018)":
                comp_data = df[
                    (df['year'] <= 2018) &
                    (df['position_rank'] <= 5) &
                    (df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                ]
                comp_label = "2014-2018"
            else:  # Recent Years (2019-2024)
                comp_data = df[
                    (df['year'] >= 2019) &
                    (df['position_rank'] <= 5) &
                    (df['position'].isin(['QB', 'RB', 'WR', 'TE']))
                ]
                comp_label = "2019-2024"
            
            st.subheader("📊 Comparison Period")
            st.write(f"**Period:** {comp_label}")
            
            if not comp_data.empty:
                comparison_summary = comp_data.groupby(['position', 'tier_label'])['auction_value_dollars'].mean().reset_index()
                
                st.dataframe(
                    comparison_summary.pivot(index='tier_label', columns='position', values='auction_value_dollars').round(2),
                    use_container_width=True
                )
        
        # Difference analysis
        if not filtered_df.empty and not comp_data.empty:
            st.subheader("📈 Price Differences")
            
            # Merge the data for comparison
            selected_summary = filtered_df[
                (filtered_df['position_rank'] <= 5) &
                (filtered_df['position'].isin(['QB', 'RB', 'WR', 'TE']))
            ].groupby('tier_label')['auction_value_dollars'].mean()
            
            comparison_summary_series = comp_data.groupby('tier_label')['auction_value_dollars'].mean()
            
            # Calculate differences
            diff_data = []
            for tier in selected_summary.index:
                if tier in comparison_summary_series.index:
                    selected_val = selected_summary[tier]
                    comp_val = comparison_summary_series[tier]
                    diff_data.append({
                        'Tier': tier,
                        'Your Period': f"${selected_val:.0f}",
                        'Comparison': f"${comp_val:.0f}",
                        'Difference': f"${selected_val - comp_val:+.0f}",
                        'Percent Change': f"{((selected_val / comp_val - 1) * 100):+.1f}%"
                    })
            
            if diff_data:
                diff_df = pd.DataFrame(diff_data)
                st.dataframe(diff_df, use_container_width=True, hide_index=True)
                
                # Visualization of differences
                fig = px.bar(
                    diff_df,
                    x='Tier',
                    y=[float(x.replace('$', '').replace('+', '').replace(',', '')) for x in diff_df['Difference']],
                    title=f"Price Differences: {year_range[0]}-{year_range[1]} vs {comp_label}",
                    labels={'y': 'Price Difference ($)'},
                    color=[float(x.replace('$', '').replace('+', '').replace(',', '')) for x in diff_df['Difference']],
                    color_continuous_scale='RdBu'
                )
                
                fig.update_layout(
                    yaxis=dict(tickformat='$,.0f'),
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary insights
                positive_changes = sum(1 for x in diff_df['Difference'] if float(x.replace('$', '').replace('+', '').replace(',', '')) > 0)
                total_changes = len(diff_df)
                
                if positive_changes > total_changes / 2:
                    trend = "📈 Higher"
                    color = "green"
                elif positive_changes < total_changes / 2:
                    trend = "📉 Lower"
                    color = "red"
                else:
                    trend = "➡️ Similar"
                    color = "blue"
                
                st.info(f"""
                **Summary:** Your selected period ({year_range[0]}-{year_range[1]}) shows **{trend}** auction values compared to {comp_label}.
                
                - **{positive_changes} out of {total_changes}** position tiers cost more in your selected period
                - This suggests auction values were {'higher' if positive_changes > total_changes/2 else 'lower' if positive_changes < total_changes/2 else 'similar'} during {year_range[0]}-{year_range[1]}
                """)
            else:
                st.warning("No overlapping tiers found for comparison.")
        else:
            st.warning("No data available for selected comparison period.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Blue Steele Fantasy Analysis** | "
        "**Data Source:** Fantasy auction results from 2014-2024 | "
        "**Built with:** Streamlit & Plotly | "
        f"**Last Updated:** {df['year'].max() if not df.empty else 'N/A'}"
    )


if __name__ == "__main__":
    main()
