#!/usr/bin/env python3
"""
Run the AFL data ingestion pipeline.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.data.ingestion.afl_tables import main as run_ingestion

if __name__ == "__main__":
    print("🏈 Starting AFL data ingestion...")
    print("This will fetch 2020-2024 season data from Squiggle API")
    print("="*60)

    run_ingestion()

    print("\n✅ Ingestion complete!")
