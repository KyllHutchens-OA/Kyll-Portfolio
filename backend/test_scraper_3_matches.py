"""Test the smart scraper with just 3 matches from 2025."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.data.ingestion.smart_scraper import SmartAFLScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("TEST: Scraping only 3 matches from 2025")
logger.info("=" * 60)

with SmartAFLScraper() as scraper:
    scraper._load_caches()

    # Manually limit to 3 matches by modifying the scraping function
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    year = 2025
    url = f"{scraper.AFL_TABLES_BASE}/seas/{year}.html"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    relative_links = [
        link['href']
        for link in soup.find_all('a', href=lambda href: href and href.startswith("../stats/games/"))
    ]

    base_url = f"{scraper.AFL_TABLES_BASE}/seas/"
    match_urls = [urljoin(base_url, link) for link in relative_links]

    logger.info(f"Found {len(match_urls)} total matches, testing with first 3...")

    added_count = 0
    for match_url in match_urls[:3]:  # Only first 3
        if scraper._scrape_single_match(match_url, year):
            added_count += 1
        import time
        time.sleep(0.5)

    scraper.session.commit()
    logger.info(f"✅ Successfully added {added_count}/3 matches")

    # Print summary
    stats = scraper.get_stats_summary()
    logger.info("=" * 60)
    logger.info(f"Total matches in database: {stats['matches']}")
    logger.info("=" * 60)
