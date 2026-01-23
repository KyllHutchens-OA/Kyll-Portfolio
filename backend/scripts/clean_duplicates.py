"""
Clean duplicate matches from the database.

Keeps the earliest created_at record and removes duplicates.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import func, and_
from app.data.database import Session
from app.data.models import Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_duplicates():
    """Find duplicate matches based on unique constraint fields."""
    session = Session()

    # Find groups with duplicates
    duplicates = (
        session.query(
            Match.season,
            Match.round,
            Match.home_team_id,
            Match.away_team_id,
            func.count(Match.id).label('count')
        )
        .group_by(Match.season, Match.round, Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    logger.info(f"Found {len(duplicates)} duplicate groups")

    total_duplicates = 0
    for dup in duplicates:
        season, round_val, home_id, away_id, count = dup
        logger.info(f"  Season {season}, Round {round_val}, Teams {home_id} vs {away_id}: {count} records")
        total_duplicates += (count - 1)  # All but one are duplicates

    logger.info(f"Total duplicate records to remove: {total_duplicates}")

    session.close()
    return duplicates


def clean_duplicates(dry_run=True):
    """Remove duplicate matches, keeping the earliest created_at."""
    session = Session()

    # Find duplicate groups
    duplicates = (
        session.query(
            Match.season,
            Match.round,
            Match.home_team_id,
            Match.away_team_id
        )
        .group_by(Match.season, Match.round, Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    removed_count = 0

    for dup in duplicates:
        season, round_val, home_id, away_id = dup

        # Get all matches in this duplicate group
        matches = (
            session.query(Match)
            .filter(
                and_(
                    Match.season == season,
                    Match.round == round_val,
                    Match.home_team_id == home_id,
                    Match.away_team_id == away_id
                )
            )
            .order_by(Match.created_at.asc())
            .all()
        )

        # Keep the first (earliest), remove the rest
        keep = matches[0]
        remove = matches[1:]

        logger.info(
            f"Season {season}, Round {round_val}, Teams {home_id} vs {away_id}: "
            f"Keeping ID {keep.id}, removing {len(remove)} duplicates"
        )

        for match in remove:
            if not dry_run:
                session.delete(match)
            removed_count += 1

    if dry_run:
        logger.info(f"DRY RUN: Would remove {removed_count} duplicate matches")
        session.rollback()
    else:
        session.commit()
        logger.info(f"✅ Removed {removed_count} duplicate matches")

    session.close()
    return removed_count


def verify_cleanup():
    """Verify that no duplicates remain."""
    session = Session()

    duplicates = (
        session.query(
            Match.season,
            Match.round,
            Match.home_team_id,
            Match.away_team_id,
            func.count(Match.id).label('count')
        )
        .group_by(Match.season, Match.round, Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    if len(duplicates) == 0:
        logger.info("✅ No duplicates found - database is clean!")
    else:
        logger.error(f"❌ Still have {len(duplicates)} duplicate groups")

    session.close()
    return len(duplicates) == 0


def main():
    logger.info("=" * 60)
    logger.info("AFL Database - Duplicate Match Cleanup")
    logger.info("=" * 60)

    # Step 1: Find duplicates
    logger.info("\n1. Finding duplicates...")
    find_duplicates()

    # Step 2: Clean (dry run first)
    logger.info("\n2. Cleaning duplicates (DRY RUN)...")
    clean_duplicates(dry_run=True)

    # Step 3: Confirm
    print("\n" + "=" * 60)
    response = input("Proceed with deletion? (yes/no): ")

    if response.lower() == 'yes':
        logger.info("\n3. Cleaning duplicates (REAL)...")
        clean_duplicates(dry_run=False)

        logger.info("\n4. Verifying cleanup...")
        verify_cleanup()
    else:
        logger.info("Aborted.")


if __name__ == "__main__":
    main()
