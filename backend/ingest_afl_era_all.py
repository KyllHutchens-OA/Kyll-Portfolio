"""
Ingest ALL AFL-era data from CSV files (1990-2024).
This will take several minutes to complete.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.data.ingestion.csv_match_ingester import CSVMatchIngester

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

csv_dir = "/Users/kyllhutchens/Code/AFL App/data/afl-data-analysis/data/matches"
AFL_START_YEAR = 1990

logger.info("=" * 80)
logger.info("AFL-ERA DATA INGESTION (1990-2024)")
logger.info("=" * 80)
logger.info("This will ingest all match data from the AFL era")
logger.info("Expected: ~7,500+ matches across 35 seasons")
logger.info("=" * 80)

with CSVMatchIngester(csv_dir) as ingester:
    current_year = 2024  # Don't include 2025, we already scraped it

    total_added = 0
    total_skipped = 0
    failed_seasons = []

    for year in range(AFL_START_YEAR, current_year + 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing season {year}")
        logger.info(f"{'='*80}")

        try:
            ingester.ingest_season(year, limit=None, dry_run=False)
            logger.info(f"✅ Completed season {year}")

        except Exception as e:
            logger.error(f"❌ Failed to ingest season {year}: {e}")
            failed_seasons.append(year)
            continue

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("INGESTION COMPLETE!")
    logger.info("=" * 80)

    if failed_seasons:
        logger.warning(f"Failed seasons: {failed_seasons}")

    # Get final stats
    stats = ingester.get_stats_summary()
    logger.info(f"Total matches in database: {stats['matches']}")
    logger.info(f"Total teams: {stats['teams']}")
    logger.info("=" * 80)
