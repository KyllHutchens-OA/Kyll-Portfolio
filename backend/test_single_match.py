"""Test scraping a single match from 2025 to verify URL construction."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the season page
year = 2025
url = f"https://afltables.com/afl/seas/{year}.html"

logger.info(f"Fetching season page: {url}")
response = requests.get(url, timeout=30)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

# Find match links
relative_links = [
    link['href']
    for link in soup.find_all('a', href=lambda href: href and href.startswith("../stats/games/"))
]

logger.info(f"Found {len(relative_links)} match links")

if relative_links:
    # Test the first match
    base_url = "https://afltables.com/afl/seas/"
    first_match_url = urljoin(base_url, relative_links[0])

    logger.info(f"\\nTesting first match URL: {first_match_url}")

    try:
        match_response = requests.get(first_match_url, timeout=15)
        match_response.raise_for_status()

        logger.info(f"✅ SUCCESS! URL is valid and returns 200")
        logger.info(f"Response length: {len(match_response.text)} bytes")

    except Exception as e:
        logger.error(f"❌ FAILED! Error: {e}")
else:
    logger.warning("No match links found!")
