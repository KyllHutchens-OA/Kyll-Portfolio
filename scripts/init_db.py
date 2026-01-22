#!/usr/bin/env python3
"""
Initialize the database schema and run migrations.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.data.database import engine, Base
from app.data.models import Team, Player, Match, PlayerStat, TeamStat, Conversation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """
    Create all database tables based on SQLAlchemy models.
    """
    logger.info("Creating database tables...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        logger.info("Tables created: teams, players, matches, player_stats, team_stats, conversations")

    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
