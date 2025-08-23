-- Fantasy Football Auction Analysis Queries
-- Use these queries to analyze positional tier trends across years

-- =============================================================================
-- BASIC POSITION TIER QUERIES
-- =============================================================================

-- View all WR1-WR5 prices by year
SELECT 
    year,
    position_rank,
    auction_value_dollars as price,
    tier_label
FROM position_tiers 
WHERE position = 'WR' AND position_rank <= 5
ORDER BY year, position_rank;

-- Average price for each WR tier across all years
SELECT 
    tier_label,
    ROUND(AVG(auction_value_dollars), 2) as avg_price,
    COUNT(*) as years_of_data
FROM position_tiers 
WHERE position = 'WR' AND position_rank <= 10
GROUP BY position_rank
ORDER BY position_rank;

-- =============================================================================
-- TREND ANALYSIS QUERIES
-- =============================================================================

-- WR1 price trend over time
SELECT 
    year,
    auction_value_dollars as wr1_price
FROM position_tiers 
WHERE position = 'WR' AND position_rank = 1
ORDER BY year;

-- Compare top tier prices across positions by year
SELECT 
    year,
    MAX(CASE WHEN position = 'QB' AND position_rank = 1 THEN auction_value_dollars END) as QB1,
    MAX(CASE WHEN position = 'RB' AND position_rank = 1 THEN auction_value_dollars END) as RB1,
    MAX(CASE WHEN position = 'WR' AND position_rank = 1 THEN auction_value_dollars END) as WR1,
    MAX(CASE WHEN position = 'TE' AND position_rank = 1 THEN auction_value_dollars END) as TE1
FROM position_tiers
WHERE position_rank = 1
GROUP BY year
ORDER BY year;

-- =============================================================================
-- POSITIONAL VALUE ANALYSIS
-- =============================================================================

-- Price dropoff from WR1 to WR2 to WR3 by year
SELECT 
    year,
    MAX(CASE WHEN position_rank = 1 THEN auction_value_dollars END) as WR1,
    MAX(CASE WHEN position_rank = 2 THEN auction_value_dollars END) as WR2,
    MAX(CASE WHEN position_rank = 3 THEN auction_value_dollars END) as WR3,
    -- Calculate dropoffs
    MAX(CASE WHEN position_rank = 1 THEN auction_value_dollars END) - 
    MAX(CASE WHEN position_rank = 2 THEN auction_value_dollars END) as WR1_to_WR2_drop,
    MAX(CASE WHEN position_rank = 2 THEN auction_value_dollars END) - 
    MAX(CASE WHEN position_rank = 3 THEN auction_value_dollars END) as WR2_to_WR3_drop
FROM position_tiers
WHERE position = 'WR' AND position_rank <= 3
GROUP BY year
ORDER BY year;

-- Average price by position tier (top 12 of each position)
SELECT 
    position,
    position_rank,
    tier_label,
    ROUND(AVG(auction_value_dollars), 2) as avg_price,
    ROUND(MIN(auction_value_dollars), 2) as min_price,
    ROUND(MAX(auction_value_dollars), 2) as max_price,
    COUNT(*) as sample_size
FROM position_tiers
WHERE position_rank <= 12
GROUP BY position, position_rank
ORDER BY position, position_rank;

-- =============================================================================
-- MARKET EFFICIENCY ANALYSIS
-- =============================================================================

-- Coefficient of variation (price volatility) by position tier
SELECT 
    position,
    position_rank,
    tier_label,
    COUNT(*) as years,
    ROUND(AVG(auction_value_dollars), 2) as avg_price,
    ROUND(
        (SELECT 
            SQRT(AVG((auction_value_dollars - sub_avg.avg_price) * (auction_value_dollars - sub_avg.avg_price)))
        FROM position_tiers pt2 
        WHERE pt2.position = pt.position AND pt2.position_rank = pt.position_rank) 
        / AVG(auction_value_dollars) * 100, 2
    ) as coefficient_of_variation_pct
FROM position_tiers pt
JOIN (
    SELECT position, position_rank, AVG(auction_value_dollars) as avg_price
    FROM position_tiers
    GROUP BY position, position_rank
) sub_avg ON pt.position = sub_avg.position AND pt.position_rank = sub_avg.position_rank
WHERE position_rank <= 5
GROUP BY position, position_rank
ORDER BY position, position_rank;

-- =============================================================================
-- RECENT TRENDS (Last 3 Years)
-- =============================================================================

-- Recent trend: 2022-2024 average vs historical average
WITH recent_avg AS (
    SELECT 
        position,
        position_rank,
        AVG(auction_value_dollars) as recent_avg_price
    FROM position_tiers
    WHERE year >= 2022 AND position_rank <= 5
    GROUP BY position, position_rank
),
historical_avg AS (
    SELECT 
        position,
        position_rank,
        AVG(auction_value_dollars) as historical_avg_price
    FROM position_tiers
    WHERE year < 2022 AND position_rank <= 5
    GROUP BY position, position_rank
)
SELECT 
    r.position,
    r.position_rank,
    r.position || r.position_rank as tier,
    ROUND(h.historical_avg_price, 2) as historical_avg,
    ROUND(r.recent_avg_price, 2) as recent_avg,
    ROUND(r.recent_avg_price - h.historical_avg_price, 2) as price_change,
    ROUND((r.recent_avg_price / h.historical_avg_price - 1) * 100, 1) as pct_change
FROM recent_avg r
JOIN historical_avg h ON r.position = h.position AND r.position_rank = h.position_rank
ORDER BY r.position, r.position_rank;

-- =============================================================================
-- USEFUL SUMMARY VIEWS
-- =============================================================================

-- Create a summary of all position tiers for easy reference
-- (This is a view you might want to create permanently)
/*
CREATE VIEW tier_summary AS
SELECT 
    position,
    position_rank,
    tier_label,
    COUNT(*) as years_of_data,
    ROUND(MIN(auction_value_dollars), 2) as min_price,
    ROUND(AVG(auction_value_dollars), 2) as avg_price,
    ROUND(MAX(auction_value_dollars), 2) as max_price,
    ROUND(
        SQRT(AVG((auction_value_dollars - avg_sub.avg_val) * (auction_value_dollars - avg_sub.avg_val))), 2
    ) as std_dev
FROM position_tiers pt
CROSS JOIN (
    SELECT position as pos, position_rank as rank, AVG(auction_value_dollars) as avg_val
    FROM position_tiers pt2
    WHERE pt2.position = pt.position AND pt2.position_rank = pt.position_rank
) avg_sub
WHERE position_rank <= 15
GROUP BY position, position_rank
ORDER BY position, position_rank;
*/
