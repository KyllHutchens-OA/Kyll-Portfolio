"""
Force clean duplicate matches - no prompts, just clean.
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


def clean_duplicates():
    """Remove duplicate matches based on (season, DATE, home, away)."""
    session = Session()

    # Find duplicate groups by DATE (not datetime)
    duplicates = (
        session.query(
            Match.season,
            func.date(Match.match_date).label('match_date_only'),
            Match.home_team_id,
            Match.away_team_id
        )
        .group_by(Match.season, func.date(Match.match_date), Match.home_team_id, Match.away_team_id)
        .having(func.count(Match.id) > 1)
        .all()
    )

    logger.info(f"Found {len(duplicates)} duplicate groups")

    removed_count = 0

    for dup in duplicates:
        season, date_only, home_id, away_id = dup

        # Get all matches in this group
        matches = (
            session.query(Match)
            .filter(
                and_(
                    Match.season == season,
                    func.date(Match.match_date) == date_only,
                    Match.home_team_id == home_id,
                    Match.away_team_id == away_id
                )
            )
            .order_by(Match.id.asc())  # Keep lowest ID (first ingested)
            .all()
        )

        if len(matches) <= 1:
            continue

        # Keep first, remove rest
        keep = matches[0]
        remove = matches[1:]

        for match in remove:
            session.delete(match)
            removed_count += 1
            logger.info(f"Removing duplicate: ID {match.id}, Round {match.round}")

    session.commit()
    logger.info(f"\n✅ Removed {removed_count} duplicate matches")

    session.close()
    return removed_count


def main():
    logger.info("Cleaning duplicate matches...")
    logger.info("")

    removed = clean_duplicates()

    logger.info("")
    logger.info(f"Done! Removed {removed} duplicates")

    # Verify
    session = Session()
    total = session.query(func.count(Match.id)).scalar()
    logger.info(f"Total matches remaining: {total}")
    session.close()


if __name__ == "__main__":
    main()
