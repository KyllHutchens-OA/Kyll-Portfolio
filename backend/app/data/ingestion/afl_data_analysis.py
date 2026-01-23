"""
AFL Data Analysis GitHub Repository Ingester.

Ingests comprehensive AFL data from: https://github.com/akareen/AFL-Data-Analysis

Data includes:
- Match results with quarter-by-quarter scoring (1897-2025)
- Player profiles (5,700+ players)
- Player statistics (682,000+ rows)
- Team lineups
"""
import requests
import csv
import io
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, date

from app.data.database import Session
from app.data.models import Team, Player, Match, PlayerStat, MatchLineup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AFLDataAnalysisIngester:
    """
    Ingester for AFL Data Analysis GitHub repository.
    """

    BASE_URL = "https://raw.githubusercontent.com/akareen/AFL-Data-Analysis/master/data"

    # Team name mappings (GitHub data -> our database)
    TEAM_MAPPINGS = {
        "Adelaide": "ADE",
        "Brisbane Lions": "BRI",
        "Carlton": "CAR",
        "Collingwood": "COL",
        "Essendon": "ESS",
        "Fremantle": "FRE",
        "Geelong": "GEE",
        "Gold Coast": "GCS",
        "Greater Western Sydney": "GWS",
        "Hawthorn": "HAW",
        "Melbourne": "MEL",
        "North Melbourne": "NM",
        "Port Adelaide": "PA",
        "Richmond": "RIC",
        "St Kilda": "STK",
        "Sydney": "SYD",
        "West Coast": "WCE",
        "Western Bulldogs": "WB",
    }

    def __init__(self):
        self.session = Session()
        self.teams_cache = {}  # Cache team IDs
        self.players_cache = {}  # Cache player IDs by name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _load_teams_cache(self):
        """Load team IDs into cache for quick lookup."""
        teams = self.session.query(Team).all()
        for team in teams:
            self.teams_cache[team.name] = team.id
            self.teams_cache[team.abbreviation] = team.id
        logger.info(f"Loaded {len(teams)} teams into cache")

    def get_team_id(self, team_identifier: str) -> Optional[int]:
        """Get team ID from cache by name or abbreviation."""
        # Try direct lookup
        if team_identifier in self.teams_cache:
            return self.teams_cache[team_identifier]

        # Try mapping
        abbrev = self.TEAM_MAPPINGS.get(team_identifier)
        if abbrev:
            return self.teams_cache.get(abbrev)

        return None

    def ingest_matches(self, start_year: int, end_year: int):
        """
        Ingest match data for specified years.

        Includes quarter-by-quarter scoring and enhanced match details.
        """
        logger.info(f"Ingesting matches from {start_year} to {end_year}...")

        if not self.teams_cache:
            self._load_teams_cache()

        for year in range(start_year, end_year + 1):
            logger.info(f"\\n{'='*60}")
            logger.info(f"Processing matches for {year}")
            logger.info(f"{'='*60}")

            url = f"{self.BASE_URL}/matches/matches_{year}.csv"

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # Parse CSV
                csv_data = csv.DictReader(io.StringIO(response.text))
                matches_added = 0

                for row in csv_data:
                    if self._process_match_row(row, year):
                        matches_added += 1

                self.session.commit()
                logger.info(f"✅ Added {matches_added} matches for {year}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {year} matches: {e}")
                self.session.rollback()
            except Exception as e:
                logger.error(f"Error processing {year} matches: {e}")
                self.session.rollback()

            time.sleep(0.5)  # Be nice to GitHub

    def _process_match_row(self, row: dict, year: int) -> bool:
        """Process a single match row from CSV."""
        try:
            # Extract team names
            team_1_name = row.get("team_1_team_name")
            team_2_name = row.get("team_2_team_name")

            team_1_id = self.get_team_id(team_1_name)
            team_2_id = self.get_team_id(team_2_name)

            if not team_1_id or not team_2_id:
                logger.warning(f"Could not find team IDs for {team_1_name} vs {team_2_name}")
                return False

            # Parse date
            date_str = row.get("date")
            try:
                match_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            except:
                match_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")

            # Round number
            round_num = int(row.get("round_num"))

            # Calculate final scores (goals * 6 + behinds)
            team_1_goals = int(row.get("team_1_final_goals") or 0)
            team_1_behinds = int(row.get("team_1_final_behinds") or 0)
            team_1_score = team_1_goals * 6 + team_1_behinds

            team_2_goals = int(row.get("team_2_final_goals") or 0)
            team_2_behinds = int(row.get("team_2_final_behinds") or 0)
            team_2_score = team_2_goals * 6 + team_2_behinds

            # Determine home/away (team_1 is home)
            home_team_id = team_1_id
            away_team_id = team_2_id
            home_score = team_1_score
            away_score = team_2_score

            # Check if match already exists
            existing_match = self.session.query(Match).filter_by(
                season=year,
                round=round_num,
                home_team_id=home_team_id,
                away_team_id=away_team_id
            ).first()

            if existing_match:
                # Update with quarter-by-quarter scores if not already set
                if not existing_match.home_q1_goals:
                    existing_match.home_q1_goals = int(row.get("team_1_q1_goals") or 0)
                    existing_match.home_q1_behinds = int(row.get("team_1_q1_behinds") or 0)
                    existing_match.home_q2_goals = int(row.get("team_1_q2_goals") or 0)
                    existing_match.home_q2_behinds = int(row.get("team_1_q2_behinds") or 0)
                    existing_match.home_q3_goals = int(row.get("team_1_q3_goals") or 0)
                    existing_match.home_q3_behinds = int(row.get("team_1_q3_behinds") or 0)
                    existing_match.home_q4_goals = team_1_goals
                    existing_match.home_q4_behinds = team_1_behinds

                    existing_match.away_q1_goals = int(row.get("team_2_q1_goals") or 0)
                    existing_match.away_q1_behinds = int(row.get("team_2_q1_behinds") or 0)
                    existing_match.away_q2_goals = int(row.get("team_2_q2_goals") or 0)
                    existing_match.away_q2_behinds = int(row.get("team_2_q2_behinds") or 0)
                    existing_match.away_q3_goals = int(row.get("team_2_q3_goals") or 0)
                    existing_match.away_q3_behinds = int(row.get("team_2_q3_behinds") or 0)
                    existing_match.away_q4_goals = team_2_goals
                    existing_match.away_q4_behinds = team_2_behinds

                    logger.debug(f"Updated Q-by-Q scores: {year} R{round_num} {team_1_name} vs {team_2_name}")
                return False

            # Create new match
            match = Match(
                season=year,
                round=round_num,
                match_date=match_date,
                venue=row.get("venue"),
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_score=home_score,
                away_score=away_score,
                # Quarter-by-quarter scoring
                home_q1_goals=int(row.get("team_1_q1_goals") or 0),
                home_q1_behinds=int(row.get("team_1_q1_behinds") or 0),
                home_q2_goals=int(row.get("team_1_q2_goals") or 0),
                home_q2_behinds=int(row.get("team_1_q2_behinds") or 0),
                home_q3_goals=int(row.get("team_1_q3_goals") or 0),
                home_q3_behinds=int(row.get("team_1_q3_behinds") or 0),
                home_q4_goals=team_1_goals,
                home_q4_behinds=team_1_behinds,
                away_q1_goals=int(row.get("team_2_q1_goals") or 0),
                away_q1_behinds=int(row.get("team_2_q1_behinds") or 0),
                away_q2_goals=int(row.get("team_2_q2_goals") or 0),
                away_q2_behinds=int(row.get("team_2_q2_behinds") or 0),
                away_q3_goals=int(row.get("team_2_q3_goals") or 0),
                away_q3_behinds=int(row.get("team_2_q3_behinds") or 0),
                away_q4_goals=team_2_goals,
                away_q4_behinds=team_2_behinds,
                match_status="completed"
            )

            self.session.add(match)
            logger.info(f"Added: {year} R{round_num} - {team_1_name} {team_1_score} vs {team_2_name} {team_2_score}")

            return True

        except Exception as e:
            logger.error(f"Error processing match row: {e}")
            logger.error(f"Row data: {row}")
            return False

    def get_stats_summary(self) -> dict:
        """Get summary statistics of ingested data."""
        teams_count = self.session.query(Team).count()
        matches_count = self.session.query(Match).count()
        players_count = self.session.query(Player).count()
        player_stats_count = self.session.query(PlayerStat).count()

        return {
            "teams": teams_count,
            "matches": matches_count,
            "players": players_count,
            "player_stats": player_stats_count,
        }


def main():
    """Main function to run the ingestion pipeline."""
    logger.info("Starting AFL Data Analysis repository ingestion...")

    with AFLDataAnalysisIngester() as ingester:
        # Ingest matches from 2020-2025
        ingester.ingest_matches(2020, 2025)

        # Print summary
        stats = ingester.get_stats_summary()
        logger.info("\\n" + "="*60)
        logger.info("INGESTION COMPLETE - Summary:")
        logger.info("="*60)
        logger.info(f"Teams: {stats['teams']}")
        logger.info(f"Matches: {stats['matches']}")
        logger.info(f"Players: {stats['players']}")
        logger.info(f"Player Stats: {stats['player_stats']}")
        logger.info("="*60)


if __name__ == "__main__":
    main()
