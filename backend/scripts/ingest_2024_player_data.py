"""
Ingest missing 2024 player statistics from CSV files.

This script reads player performance CSV files and ingests only 2024 season data
that's currently missing from the database.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
engine = create_engine(os.getenv("DB_STRING"))

# Path to player CSV files
PLAYERS_DIR = Path("/Users/kyllhutchens/Code/AFL App/data/afl-data-analysis/data/players")

def get_team_id(team_name: str, conn) -> int:
    """Get team ID from database."""
    # Map common team name variations
    team_mapping = {
        "Greater Western Sydney": "Greater Western Sydney",
        "GWS": "Greater Western Sydney",
        "Western Bulldogs": "Western Bulldogs",
        "Bulldogs": "Western Bulldogs",
        "Brisbane Lions": "Brisbane Lions",
        "Brisbane": "Brisbane Lions",
        "North Melbourne": "North Melbourne",
        "Kangaroos": "North Melbourne",
        "Port Adelaide": "Port Adelaide",
        "West Coast": "West Coast",
        "Gold Coast": "Gold Coast"
    }

    search_name = team_mapping.get(team_name, team_name)

    result = conn.execute(
        text("SELECT id FROM teams WHERE name ILIKE :name LIMIT 1"),
        {"name": search_name}
    )
    row = result.fetchone()
    if row:
        return row[0]

    logger.warning(f"Team not found: {team_name} (searched: {search_name})")
    return None

def get_or_create_player(player_name: str, team_id: int, conn) -> int:
    """Get existing player ID or create new player."""
    # Check if player exists
    result = conn.execute(
        text("SELECT id FROM players WHERE name ILIKE :name LIMIT 1"),
        {"name": player_name}
    )
    row = result.fetchone()

    if row:
        return row[0]

    # Create new player
    result = conn.execute(
        text("""
            INSERT INTO players (name, team_id, created_at, updated_at)
            VALUES (:name, :team_id, :now, :now)
            RETURNING id
        """),
        {"name": player_name, "team_id": team_id, "now": datetime.now()}
    )
    conn.commit()
    return result.fetchone()[0]

def get_match_id(team_id: int, opponent: str, season: int, round_num: str, conn) -> int:
    """Get match ID by matching team, opponent, season, and round."""
    # Get opponent team ID
    opponent_id = get_team_id(opponent, conn)
    if not opponent_id:
        return None

    # Find match where team was home or away
    result = conn.execute(
        text("""
            SELECT id FROM matches
            WHERE season = :season
            AND round = :round
            AND ((home_team_id = :team_id AND away_team_id = :opponent_id)
                 OR (away_team_id = :team_id AND home_team_id = :opponent_id))
            LIMIT 1
        """),
        {
            "season": season,
            "round": round_num,
            "team_id": team_id,
            "opponent_id": opponent_id
        }
    )
    row = result.fetchone()
    return row[0] if row else None

def ingest_2024_data():
    """Ingest all 2024 player statistics from CSV files."""

    # Find all performance CSV files
    csv_files = list(PLAYERS_DIR.glob("*_performance_details.csv"))
    logger.info(f"Found {len(csv_files)} player CSV files")

    total_stats = 0
    total_players = 0
    skipped_no_match = 0

    with engine.connect() as conn:
        for csv_file in csv_files:
            try:
                # Read CSV
                df = pd.read_csv(csv_file)

                # Filter for 2024 season only
                df_2024 = df[df['year'] == 2024]

                if len(df_2024) == 0:
                    continue  # No 2024 data for this player

                # Extract player name from filename
                # Format: lastname_firstname_ddmmyyyy_performance_details.csv
                filename_parts = csv_file.stem.split('_')
                if len(filename_parts) < 3:
                    logger.warning(f"Invalid filename format: {csv_file.name}")
                    continue

                last_name = filename_parts[0].capitalize()
                first_name = filename_parts[1].capitalize()
                player_name = f"{first_name} {last_name}"

                # Get team ID from first row
                team_name = df_2024.iloc[0]['team']
                team_id = get_team_id(team_name, conn)

                if not team_id:
                    logger.warning(f"Skipping {player_name} - team not found: {team_name}")
                    continue

                # Get or create player
                player_id = get_or_create_player(player_name, team_id, conn)
                total_players += 1

                # Insert player stats for each game
                for _, row in df_2024.iterrows():
                    # Get match ID
                    match_id = get_match_id(
                        team_id,
                        row['opponent'],
                        2024,
                        row['round'],
                        conn
                    )

                    if not match_id:
                        skipped_no_match += 1
                        continue

                    # Insert player stats
                    conn.execute(
                        text("""
                            INSERT INTO player_stats (
                                match_id, player_id, disposals, kicks, handballs,
                                marks, tackles, goals, behinds, hitouts, clearances,
                                inside_50s, rebound_50s, contested_possessions,
                                uncontested_possessions, contested_marks, marks_inside_50,
                                one_percenters, clangers, free_kicks_for, free_kicks_against,
                                brownlow_votes, time_on_ground_pct
                            ) VALUES (
                                :match_id, :player_id, :disposals, :kicks, :handballs,
                                :marks, :tackles, :goals, :behinds, :hitouts, :clearances,
                                :inside_50s, :rebound_50s, :contested_possessions,
                                :uncontested_possessions, :contested_marks, :marks_inside_50,
                                :one_percenters, :clangers, :free_kicks_for, :free_kicks_against,
                                :brownlow_votes, :time_on_ground_pct
                            )
                            ON CONFLICT (match_id, player_id) DO NOTHING
                        """),
                        {
                            "match_id": match_id,
                            "player_id": player_id,
                            "disposals": row.get('disposals') or None,
                            "kicks": row.get('kicks') or None,
                            "handballs": row.get('handballs') or None,
                            "marks": row.get('marks') or None,
                            "tackles": row.get('tackles') or None,
                            "goals": row.get('goals') or None,
                            "behinds": row.get('behinds') or None,
                            "hitouts": row.get('hit_outs') or None,
                            "clearances": row.get('clearances') or None,
                            "inside_50s": row.get('inside_50s') or None,
                            "rebound_50s": row.get('rebound_50s') or None,
                            "contested_possessions": row.get('contested_possessions') or None,
                            "uncontested_possessions": row.get('uncontested_possessions') or None,
                            "contested_marks": row.get('contested_marks') or None,
                            "marks_inside_50": row.get('marks_inside_50') or None,
                            "one_percenters": row.get('one_percenters') or None,
                            "clangers": row.get('clangers') or None,
                            "free_kicks_for": row.get('free_kicks_for') or None,
                            "free_kicks_against": row.get('free_kicks_against') or None,
                            "brownlow_votes": row.get('brownlow_votes') or None,
                            "time_on_ground_pct": row.get('percentage_of_game_played') or None
                        }
                    )
                    total_stats += 1

                conn.commit()

                if total_players % 100 == 0:
                    logger.info(f"Processed {total_players} players, {total_stats} stats")

            except Exception as e:
                logger.error(f"Error processing {csv_file.name}: {e}")
                continue

    logger.info("=" * 80)
    logger.info(f"✅ Ingestion complete!")
    logger.info(f"   Players with 2024 data: {total_players}")
    logger.info(f"   Total stats ingested: {total_stats}")
    logger.info(f"   Skipped (no matching match): {skipped_no_match}")
    logger.info("=" * 80)

if __name__ == "__main__":
    logger.info("Starting 2024 player data ingestion...")
    ingest_2024_data()
