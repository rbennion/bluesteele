#!/usr/bin/env python3
"""
Fantasy Football Auction Database Creator

This script creates a SQLite database from fantasy auction CSV data,
calculating positional rankings (WR1, WR2, etc.) for trend analysis.
"""

import sqlite3
import csv
import re
import os
from typing import List, Tuple, Dict


def parse_player_position(player_and_position: str) -> Tuple[str, str]:
    """
    Extract position from the player_and_position field.
    
    Examples:
    "Adams, Davante NYJ WR" -> ("Adams, Davante", "WR")
    "49ers, San Francisco SFO Def" -> ("49ers, San Francisco", "Def")
    """
    # Split by spaces and take the last part as position
    parts = player_and_position.strip().split()
    if len(parts) >= 2:
        position = parts[-1]
        # Join everything except the last part as player name
        player_name = ' '.join(parts[:-1])
        return player_name, position
    else:
        return player_and_position, "UNKNOWN"


def parse_auction_value(value_str: str) -> int:
    """
    Convert auction value string to cents (integer).
    
    Examples:
    "$105 " -> 10500
    "$1 " -> 100
    """
    # Remove $ and any whitespace, convert to cents
    cleaned = value_str.replace('$', '').replace(',', '').strip()
    try:
        dollars = float(cleaned)
        return int(dollars * 100)  # Convert to cents
    except ValueError:
        print(f"Warning: Could not parse auction value '{value_str}', using 0")
        return 0


def create_database(db_path: str) -> sqlite3.Connection:
    """Create the SQLite database with our schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create main table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auction_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT NOT NULL,
            auction_value INTEGER NOT NULL,
            year INTEGER NOT NULL,
            position_rank INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_position_year ON auction_data(position, year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_position_rank ON auction_data(position, position_rank)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON auction_data(year)")
    
    # Create view for easy querying
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS position_tiers AS
        SELECT 
            position,
            position_rank,
            year,
            auction_value / 100.0 as auction_value_dollars,
            position || position_rank as tier_label
        FROM auction_data
        ORDER BY year, position, position_rank
    """)
    
    conn.commit()
    return conn


def process_csv_data(csv_path: str) -> List[Tuple[str, int, int]]:
    """
    Process CSV data and return list of (position, auction_value_cents, year) tuples.
    """
    data = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM
        reader = csv.DictReader(file)
        
        for row in reader:
            player_and_position = row['Player and Position']
            auction_value_str = row['Auction Value']
            year = int(row['Year'])
            
            # Parse position
            player_name, position = parse_player_position(player_and_position)
            
            # Parse auction value
            auction_value_cents = parse_auction_value(auction_value_str)
            
            # Skip rows with zero value (likely parsing errors)
            if auction_value_cents > 0:
                data.append((position, auction_value_cents, year))
    
    return data


def calculate_position_rankings(data: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int, int]]:
    """
    Calculate position rankings within each year.
    Returns list of (position, auction_value_cents, year, position_rank) tuples.
    """
    # Group by year and position
    year_position_data: Dict[int, Dict[str, List[int]]] = {}
    
    for position, auction_value, year in data:
        if year not in year_position_data:
            year_position_data[year] = {}
        if position not in year_position_data[year]:
            year_position_data[year][position] = []
        
        year_position_data[year][position].append(auction_value)
    
    # Calculate rankings
    ranked_data = []
    
    for year, positions in year_position_data.items():
        for position, values in positions.items():
            # Sort values in descending order (highest auction value = rank 1)
            sorted_values = sorted(values, reverse=True)
            
            for rank, auction_value in enumerate(sorted_values, 1):
                ranked_data.append((position, auction_value, year, rank))
    
    return ranked_data


def insert_data(conn: sqlite3.Connection, ranked_data: List[Tuple[str, int, int, int]]):
    """Insert ranked data into the database."""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM auction_data")
    
    # Insert new data
    cursor.executemany("""
        INSERT INTO auction_data (position, auction_value, year, position_rank)
        VALUES (?, ?, ?, ?)
    """, ranked_data)
    
    conn.commit()


def print_summary(conn: sqlite3.Connection):
    """Print a summary of the imported data."""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("DATABASE IMPORT SUMMARY")
    print("="*50)
    
    # Total records
    cursor.execute("SELECT COUNT(*) FROM auction_data")
    total_records = cursor.fetchone()[0]
    print(f"Total records imported: {total_records}")
    
    # Years covered
    cursor.execute("SELECT MIN(year), MAX(year) FROM auction_data")
    min_year, max_year = cursor.fetchone()
    print(f"Years covered: {min_year} - {max_year}")
    
    # Positions and counts
    cursor.execute("""
        SELECT position, COUNT(*) as count 
        FROM auction_data 
        GROUP BY position 
        ORDER BY count DESC
    """)
    print(f"\nPositions found:")
    for position, count in cursor.fetchall():
        print(f"  {position}: {count} players")
    
    # Sample of top players by position for latest year
    cursor.execute("SELECT MAX(year) FROM auction_data")
    latest_year = cursor.fetchone()[0]
    
    print(f"\nTop 3 players by position for {latest_year}:")
    for position in ['QB', 'RB', 'WR', 'TE']:
        cursor.execute("""
            SELECT position_rank, auction_value/100.0 as price
            FROM auction_data 
            WHERE position = ? AND year = ? AND position_rank <= 3
            ORDER BY position_rank
        """, (position, latest_year))
        
        results = cursor.fetchall()
        if results:
            print(f"  {position}:")
            for rank, price in results:
                print(f"    {position}{rank}: ${price:.0f}")


def main():
    """Main function to create database and import data."""
    # File paths
    csv_path = "/Users/rbennion/Documents/lutwak-blue-steele/data/WSOFF through 2024 Raw Data.csv"
    db_path = "/Users/rbennion/Documents/lutwak-blue-steele/fantasy_auction.db"
    
    print("Creating Fantasy Football Auction Database...")
    print(f"Reading data from: {csv_path}")
    print(f"Creating database: {db_path}")
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        return
    
    # Create database
    conn = create_database(db_path)
    
    # Process CSV data
    print("\nProcessing CSV data...")
    raw_data = process_csv_data(csv_path)
    print(f"Found {len(raw_data)} valid auction entries")
    
    # Calculate rankings
    print("Calculating positional rankings...")
    ranked_data = calculate_position_rankings(raw_data)
    print(f"Calculated rankings for {len(ranked_data)} entries")
    
    # Insert into database
    print("Inserting data into database...")
    insert_data(conn, ranked_data)
    
    # Print summary
    print_summary(conn)
    
    print(f"\n✅ Database successfully created at: {db_path}")
    print("\nYou can now run queries like:")
    print("  SELECT * FROM position_tiers WHERE position = 'WR' AND position_rank <= 5;")
    
    conn.close()


if __name__ == "__main__":
    main()
