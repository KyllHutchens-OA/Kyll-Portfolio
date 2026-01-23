"""
Clean duplicate matches from the database based on match date.

Issue: Same match (date + teams) appears twice with different round numbers.
Solution: Keep the record with the lower round number, delete the higher one.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import func, and_
from app.data.database import Session
from app.data.models import Match

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def find_date_duplicates():
    """Find duplicate matches based on (season, date, teams)."""
    session = Session()

    # Find groups with duplicates
    duplicates = (
        session.query(
            Match.season,
            Match.match_date,
            Match.home_team_id,
            Match.away_team_id,
            func.count(Match.id).label('count')
        )
        .group_by(Match.season, Match.match_date, Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    logger.info(f"Found {len(duplicates)} duplicate match groups (same date + teams)")

    total_duplicates = 0
    for dup in duplicates[:10]:  # Show first 10
        season, date, home_id, away_id, count = dup
        logger.info(f"  {date.date()}: Season {season}, Teams {home_id} vs {away_id} - {count} records")
        total_duplicates += (count - 1)

    if len(duplicates) > 10:
        logger.info(f"  ... and {len(duplicates) - 10} more")

    logger.info(f"Total duplicate records to remove: {total_duplicates}")

    session.close()
    return duplicates


def clean_date_duplicates(dry_run=True):
    """Remove duplicate matches, keeping the one with the lower round number."""
    session = Session()

    # Find duplicate groups
    duplicates = (
        session.query(
            Match.season,
            Match.match_date,
            Match.home_team_id,
            Match.away_team_id
        )
        .group_by(Match.season, Match.match_date, Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    removed_count = 0

    for dup in duplicates:
        season, date, home_id, away_id = dup

        # Get all matches in this duplicate group
        matches = (
            session.query(Match)
            .filter(
                and_(
                    Match.season == season,
                    Match.match_date == date,
                    Match.home_team_id == home_id,
                    Match.away_team_id == away_id
                )
            )
            .order_by(Match.created_at.asc())  # Sort by creation time (first ingested = keep)
            .all()
        )

        if len(matches) <= 1:
            continue

        # Keep the first (lowest round number), remove the rest
        keep = matches[0]
        remove = matches[1:]

        logger.info(
            f"{date.date()}: Season {season}, Teams {home_id} vs {away_id} - "
            f"Keeping Round {keep.round}, removing {[m.round for m in remove]}"
        )

        for match in remove:
            if not dry_run:
                session.delete(match)
            removed_count += 1

    if dry_run:
        logger.info(f"\nDRY RUN: Would remove {removed_count} duplicate matches")
        session.rollback()
    else:
        session.commit()
        logger.info(f"\n✅ Removed {removed_count} duplicate matches")

    session.close()
    return removed_count


def verify_cleanup():
    """Verify that no date-based duplicates remain."""
    session = Session()

    duplicates = (
        session.query(
            Match.season,
            Match.match_date,
            Match.home_team_id,
            Match.away_team_id,
            func.count(Match.id).label('count')
        )
        .group_by(Match.season, Match.match_date, Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    if len(duplicates) == 0:
        logger.info("✅ No date-based duplicates found - database is clean!")

        # Show match count
        total = session.query(func.count(Match.id)).scalar()
        logger.info(f"Total matches in database: {total}")
    else:
        logger.error(f"❌ Still have {len(duplicates)} duplicate groups")

    session.close()
    return len(duplicates) == 0


def main():
    logger.info("=" * 60)
    logger.info("AFL Database - Date-Based Duplicate Match Cleanup")
    logger.info("=" * 60)
    logger.info("")

    # Step 1: Find duplicates
    logger.info("1. Finding duplicates (same date + teams, different rounds)...")
    logger.info("")
    find_date_duplicates()
    logger.info("")

    # Step 2: Clean (dry run first)
    logger.info("2. Cleaning duplicates (DRY RUN - no changes)...")
    logger.info("")
    clean_date_duplicates(dry_run=True)
    logger.info("")

    # Step 3: Actually clean
    logger.info("3. Cleaning duplicates (REAL - will delete)...")
    logger.info("")
    clean_date_duplicates(dry_run=False)
    logger.info("")

    # Step 4: Verify
    logger.info("4. Verifying cleanup...")
    logger.info("")
    verify_cleanup()


if __name__ == "__main__":
    main()
