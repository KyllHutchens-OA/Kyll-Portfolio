"""Scrape full 2025 season from AFL Tables."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.data.ingestion.smart_scraper import SmartAFLScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("SCRAPING FULL 2025 SEASON")
logger.info("=" * 60)

with SmartAFLScraper() as scraper:
    # Only scrape 2025
    scraper._load_caches()
    scraper._scrape_season_matches(2025)

    # Print summary
    stats = scraper.get_stats_summary()
    logger.info("\n" + "="*60)
    logger.info("DATABASE SUMMARY:")
    logger.info("="*60)
    logger.info(f"Teams: {stats['teams']}")
    logger.info(f"Matches: {stats['matches']}")
    logger.info(f"Players: {stats['players']}")
    logger.info(f"Player Stats: {stats['player_stats']}")
    logger.info("="*60)
