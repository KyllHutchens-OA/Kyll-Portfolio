"""
Smart Incremental AFL Data Scraper

Intelligently scrapes only missing data from AFL Tables.
- Only fetches AFL-era data (1990+)
- Checks database for existing records
- Handles duplicate player names using birth date
- Can be run repeatedly - only gets what's new
"""
import requests
from bs4 import BeautifulSoup
import csv
import io
import time
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import re

from app.data.database import Session
from app.data.models import Team, Player, Match, PlayerStat, MatchLineup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartAFLScraper:
    """
    Intelligent scraper that only fetches missing AFL data.
    """

    AFL_TABLES_BASE = "https://afltables.com/afl"
    AFL_START_YEAR = 1990  # AFL was renamed in 1990

    # Team name mappings (AFL Tables -> our database)
    TEAM_MAPPINGS = {
        "Adelaide": "ADE",
        "Brisbane Lions": "BRI",
        "Brisbane Bears": "BRI",  # Became Brisbane Lions in 1997
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
        "Footscray": "WB",  # Renamed to Western Bulldogs in 1997
    }

    def __init__(self):
        self.session = Session()
        self.teams_cache = {}
        self.existing_players = {}  # Cache of existing players by (first, last, dob)
        self.existing_matches = set()  # Cache of existing match identifiers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _load_caches(self):
        """Load existing data into caches to avoid duplicates."""
        logger.info("Loading existing data from database...")

        # Load teams
        teams = self.session.query(Team).all()
        for team in teams:
            self.teams_cache[team.name] = team.id
            self.teams_cache[team.abbreviation] = team.id

        # Load existing players (by first_name, last_name, date_of_birth)
        players = self.session.query(Player).all()
        for player in players:
            if player.first_name and player.last_name and player.date_of_birth:
                key = (player.first_name.lower(), player.last_name.lower(), player.date_of_birth)
                self.existing_players[key] = player.id

        # Load existing matches (by season, round, teams)
        matches = self.session.query(Match).all()
        for match in matches:
            key = (match.season, match.round, match.home_team_id, match.away_team_id)
            self.existing_matches.add(key)

        logger.info(f"Loaded: {len(self.teams_cache)} teams, {len(self.existing_players)} players, {len(self.existing_matches)} matches")

    def get_team_id(self, team_name: str) -> Optional[int]:
        """Get team ID from cache."""
        # Try direct lookup
        if team_name in self.teams_cache:
            return self.teams_cache[team_name]

        # Try mapping
        abbrev = self.TEAM_MAPPINGS.get(team_name)
        if abbrev:
            return self.teams_cache.get(abbrev)

        return None

    def get_missing_seasons(self, end_year: Optional[int] = None) -> List[int]:
        """
        Determine which seasons need to be scraped.

        Returns seasons from AFL start (1990) to current year that have
        incomplete data in the database.
        """
        if end_year is None:
            end_year = datetime.now().year

        # Get seasons we have matches for
        existing_seasons = self.session.query(Match.season).distinct().all()
        existing_seasons = {s[0] for s in existing_seasons}

        # Determine which seasons might be incomplete
        missing_seasons = []
        for year in range(self.AFL_START_YEAR, end_year + 1):
            if year not in existing_seasons:
                missing_seasons.append(year)
                logger.info(f"Season {year}: No data - will scrape")
            else:
                # Check if season is complete (should have ~200+ matches)
                match_count = self.session.query(Match).filter(Match.season == year).count()
                if match_count < 200:
                    missing_seasons.append(year)
                    logger.info(f"Season {year}: Only {match_count} matches - will scrape for missing data")

        return sorted(missing_seasons)

    def scrape_missing_matches(self, end_year: Optional[int] = None):
        """
        Scrape matches for seasons with incomplete data.
        """
        logger.info("=== SCRAPING MISSING MATCHES ===")

        if not self.teams_cache:
            self._load_caches()

        missing_seasons = self.get_missing_seasons(end_year)

        if not missing_seasons:
            logger.info("✅ All seasons have complete match data!")
            return

        logger.info(f"Will scrape {len(missing_seasons)} seasons: {missing_seasons}")

        for year in missing_seasons:
            self._scrape_season_matches(year)
            time.sleep(2)  # Be nice to AFL Tables

    def _scrape_season_matches(self, year: int):
        """Scrape all matches for a given season."""
        logger.info(f"\\n{'='*60}")
        logger.info(f"Scraping matches for {year}")
        logger.info(f"{'='*60}")

        url = f"{self.AFL_TABLES_BASE}/seas/{year}.html"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find match links the same way as the original scraper
            # Look for links starting with "../stats/games/"
            from urllib.parse import urljoin

            relative_links = [
                link['href']
                for link in soup.find_all('a', href=lambda href: href and href.startswith("../stats/games/"))
            ]

            # Construct absolute URLs using urljoin
            base_url = f"{self.AFL_TABLES_BASE}/seas/"
            match_urls = [urljoin(base_url, link) for link in relative_links]

            logger.info(f"Found {len(match_urls)} match links for {year}")

            added_count = 0
            for match_url in match_urls:
                if self._scrape_single_match(match_url, year):
                    added_count += 1
                time.sleep(0.5)  # Rate limiting

            self.session.commit()
            logger.info(f"✅ Added {added_count} new matches for {year}")

        except Exception as e:
            logger.error(f"Error scraping {year} season: {e}")
            self.session.rollback()

    def _scrape_single_match(self, url: str, year: int) -> bool:
        """Scrape a single match and add to database if not exists."""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract match details
            tables = soup.find_all('table')
            if not tables:
                return False

            # Parse match info from first table
            match_info = tables[0].find_all('td')
            if len(match_info) < 13:
                return False

            # Extract round, venue, date
            info_text = match_info[1].text
            round_match = re.search(r'Round: (.+?) Venue:', info_text)
            venue_match = re.search(r'Venue: (.+?) Date:', info_text)
            date_match = re.search(r'Date: (.+?)(?:Attendance:|$)', info_text)

            if not (round_match and venue_match and date_match):
                return False

            round_str = round_match.group(1).strip()
            venue = venue_match.group(1).strip()
            date_str = date_match.group(1).strip()

            # Parse date
            try:
                # Remove day of week and time info, just get the date
                date_clean = re.search(r'(\d+-\w+-\d{4})', date_str)
                if date_clean:
                    match_date = datetime.strptime(date_clean.group(1), '%d-%b-%Y')
                else:
                    match_date = datetime.now()
            except:
                match_date = datetime.now()

            # Extract team names and scores
            team_data = [td.text.strip() for td in match_info[3:13]]

            if len(team_data) < 10:
                return False

            team1_name = team_data[0]
            team2_name = team_data[5]

            team1_id = self.get_team_id(team1_name)
            team2_id = self.get_team_id(team2_name)

            if not (team1_id and team2_id):
                logger.debug(f"Could not find teams: {team1_name} / {team2_name}")
                return False

            # Check if match already exists
            match_key = (year, round_str, team1_id, team2_id)
            if match_key in self.existing_matches:
                return False

            # Parse quarter scores
            def parse_score(score_str):
                if '.' not in score_str:
                    return 0, 0
                parts = score_str.split('.')
                return int(parts[0]), int(parts[1])

            team1_q1_g, team1_q1_b = parse_score(team_data[1])
            team1_q2_g, team1_q2_b = parse_score(team_data[2])
            team1_q3_g, team1_q3_b = parse_score(team_data[3])
            team1_final_g, team1_final_b = parse_score(team_data[4])

            team2_q1_g, team2_q1_b = parse_score(team_data[6])
            team2_q2_g, team2_q2_b = parse_score(team_data[7])
            team2_q3_g, team2_q3_b = parse_score(team_data[8])
            team2_final_g, team2_final_b = parse_score(team_data[9])

            # Calculate final scores
            team1_score = team1_final_g * 6 + team1_final_b
            team2_score = team2_final_g * 6 + team2_final_b

            # Create match
            match = Match(
                season=year,
                round=round_str,
                match_date=match_date,
                venue=venue,
                home_team_id=team1_id,
                away_team_id=team2_id,
                home_score=team1_score,
                away_score=team2_score,
                home_q1_goals=team1_q1_g,
                home_q1_behinds=team1_q1_b,
                home_q2_goals=team1_q2_g,
                home_q2_behinds=team1_q2_b,
                home_q3_goals=team1_q3_g,
                home_q3_behinds=team1_q3_b,
                home_q4_goals=team1_final_g,
                home_q4_behinds=team1_final_b,
                away_q1_goals=team2_q1_g,
                away_q1_behinds=team2_q1_b,
                away_q2_goals=team2_q2_g,
                away_q2_behinds=team2_q2_b,
                away_q3_goals=team2_q3_g,
                away_q3_behinds=team2_q3_b,
                away_q4_goals=team2_final_g,
                away_q4_behinds=team2_final_b,
                match_status="completed"
            )

            self.session.add(match)
            self.existing_matches.add(match_key)

            logger.info(f"Added: {year} {round_str} - {team1_name} {team1_score} vs {team2_name} {team2_score}")
            return True

        except Exception as e:
            logger.error(f"Error scraping match {url}: {e}")
            return False

    def scrape_player_stats_for_season(self, year: int, player_first: str, player_last: str, player_dob: datetime.date):
        """
        Scrape player statistics for a specific season.
        Uses the local CSV files from the downloaded repo.
        """
        # Format birth date for filename
        dob_str = player_dob.strftime('%d%m%Y')
        filename = f"{player_last.lower()}_{player_first.lower()}_{dob_str}_performance_details.csv"
        filepath = f"/Users/kyllhutchens/Code/AFL App/data/afl-data-analysis/data/players/{filename}"

        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if int(row['year']) == year:
                        # Process this game's stats
                        # This will be implemented in the full version
                        pass
        except FileNotFoundError:
            logger.debug(f"No stats file for {player_first} {player_last}")
        except Exception as e:
            logger.error(f"Error reading player stats: {e}")

    def get_stats_summary(self) -> dict:
        """Get summary of database contents."""
        return {
            "teams": self.session.query(Team).count(),
            "players": self.session.query(Player).count(),
            "matches": self.session.query(Match).count(),
            "player_stats": self.session.query(PlayerStat).count(),
        }


def main():
    """Run the smart scraper."""
    logger.info("=== SMART AFL DATA SCRAPER ===")
    logger.info(f"Scraping AFL-era data ({SmartAFLScraper.AFL_START_YEAR}+)")
    logger.info("")

    with SmartAFLScraper() as scraper:
        # Scrape missing matches
        scraper.scrape_missing_matches()

        # Print summary
        stats = scraper.get_stats_summary()
        logger.info("\\n" + "="*60)
        logger.info("DATABASE SUMMARY:")
        logger.info("="*60)
        logger.info(f"Teams: {stats['teams']}")
        logger.info(f"Matches: {stats['matches']}")
        logger.info(f"Players: {stats['players']}")
        logger.info(f"Player Stats: {stats['player_stats']}")
        logger.info("="*60)


if __name__ == "__main__":
    main()
