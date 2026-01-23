"""Run full 2025 season ingestion."""
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from app.data.ingestion.csv_match_ingester import CSVMatchIngester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

csv_dir = "/Users/kyllhutchens/Code/AFL App/data/afl-data-analysis/data/matches"

logger.info("=" * 60)
logger.info("INGESTING FULL 2025 SEASON")
logger.info("=" * 60)

with CSVMatchIngester(csv_dir) as ingester:
    ingester.ingest_season(2025, limit=None, dry_run=False)

logger.info("=" * 60)
logger.info("DONE!")
logger.info("=" * 60)
