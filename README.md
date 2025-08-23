# 💙 Blue Steele Fantasy Analysis

A fantasy football auction analysis dashboard built with Streamlit, inspired by the iconic "Blue Steel" look from Zoolander.

## 🚀 Live Demo

**[View Dashboard](https://bluesteele.streamlit.app)** *(Live once deployed)*

## 📊 Features

- **Positional Tier Analysis**: Automatically ranks players (WR1, WR2, WR3, etc.) by auction value within each year
- **Multi-Year Trends**: Track how position values change over time (2014-2024)
- **Interactive Charts**:
  - Trend lines for position tiers over time
  - Heatmaps comparing positions across years
  - Value dropoff analysis between tiers
  - Price volatility analysis
- **Dynamic Filtering**: Filter by year range, positions, and tier depth
- **Comprehensive Metrics**: Average prices, volatility, and tier comparisons

## 🚀 Quick Start

### Option 1: Use the Launcher Script

```bash
./run_dashboard.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv fantasy_dashboard_env
source fantasy_dashboard_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database (if not exists)
python3 create_fantasy_database.py

# Launch dashboard
streamlit run fantasy_dashboard.py
```

The dashboard will open at: **http://localhost:8501**

## 📁 Project Structure

```
lutwak-blue-steele/
├── data/
│   └── WSOFF through 2024 Raw Data.csv    # Source CSV data
├── fantasy_auction.db                      # SQLite database (generated)
├── fantasy_dashboard.py                    # Main Streamlit dashboard
├── create_fantasy_database.py              # Database creation script
├── sample_queries.sql                      # Example SQL queries
├── run_dashboard.sh                        # Easy launcher script
├── requirements.txt                        # Python dependencies
├── fantasy_dashboard_env/                  # Virtual environment
└── README.md                              # This file
```

## 🎯 Dashboard Tabs

### 📈 Trends Over Time

- Line charts showing how WR1, WR2, etc. prices change by year
- Filterable by position and tier depth
- Data table with exact values

### 📊 Position Comparison

- Heatmap comparing QB1 vs RB1 vs WR1 vs TE1 across years
- Quick visual comparison of positional values
- Summary statistics table

### 🔥 Tier Analysis

- Bar charts for individual position analysis by year
- Compare WR1-WR12 prices for any given year
- Detailed tier breakdown

### 📉 Value Dropoffs

- Analysis of price drops between tiers (WR1 → WR2 → WR3)
- Identifies the steepest value cliffs
- Percentage and dollar dropoff calculations

### ⚡ Volatility Analysis

- Scatter plot showing price volatility vs average value
- Identifies boom/bust players vs consistent performers
- Coefficient of variation analysis

## 📋 Key Insights Available

**Position Tier Pricing:**

- WR1 averages $202 (2014-2024)
- WR2 averages $150 (-$52 dropoff)
- WR3 averages $125 (-$25 dropoff)

**Trend Analysis:**

- Track inflation/deflation in auction values
- Identify which positions have become more/less expensive
- Compare recent trends vs historical averages

**Value Analysis:**

- Find the biggest value dropoffs between tiers
- Identify consistent vs volatile position tiers
- Optimize auction strategy based on historical data

## 🛠 Database Schema

The SQLite database contains a simplified schema optimized for positional analysis:

```sql
CREATE TABLE auction_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position TEXT NOT NULL,           -- 'WR', 'RB', 'QB', 'TE', 'Def', 'TMPK'
    auction_value INTEGER NOT NULL,   -- Value in cents
    year INTEGER NOT NULL,            -- Auction year
    position_rank INTEGER NOT NULL,   -- 1=WR1, 2=WR2, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Updating Data

To add new auction data:

1. Add new rows to the CSV file
2. Run: `python3 create_fantasy_database.py`
3. Restart the dashboard

## 📝 Sample Queries

See `sample_queries.sql` for 20+ example queries you can run directly on the database:

```sql
-- Average WR1-WR5 prices across all years
SELECT tier_label, ROUND(AVG(auction_value_dollars), 2) as avg_price
FROM position_tiers
WHERE position = 'WR' AND position_rank <= 5
GROUP BY position_rank ORDER BY position_rank;

-- Recent vs historical price trends
-- (See sample_queries.sql for full query)
```

## 🎯 Use Cases

- **Auction Preparation**: Know typical tier pricing
- **Value Analysis**: Find tier dropoffs and sweet spots
- **Trend Analysis**: Identify position inflation/deflation
- **Strategy Planning**: Optimize budget allocation by position
- **Historical Research**: Compare current values to past years

---

**Built with:** Python, Streamlit, Plotly, SQLite, Pandas
**Data:** 11 years of fantasy auction results (2014-2024)
**Updated:** 2024
