"""
Quick script to scrape only 2025 season data.
"""
import sys
sys.path.insert(0, 'backend')

from app.data.ingestion.smart_scraper import SmartAFLScraper

def main():
    print("=== SCRAPING 2025 SEASON ONLY ===")

    with SmartAFLScraper() as scraper:
        scraper._load_caches()

        # Only scrape 2025
        scraper._scrape_season_matches(2025)

        # Print summary
        stats = scraper.get_stats_summary()
        print("\n" + "="*60)
        print("DATABASE SUMMARY:")
        print("="*60)
        print(f"Teams: {stats['teams']}")
        print(f"Matches: {stats['matches']}")
        print(f"Players: {stats['players']}")
        print(f"Player Stats: {stats['player_stats']}")
        print("="*60)

if __name__ == "__main__":
    main()
