"""
SQLAlchemy models for AFL analytics database.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.data.database import Base


class Team(Base):
    """AFL Team model."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    abbreviation = Column(String(10), nullable=False, unique=True)
    stadium = Column(String(100))
    primary_color = Column(String(7))
    secondary_color = Column(String(7))
    founded_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    players = relationship("Player", back_populates="team")
    home_matches = relationship(
        "Match", foreign_keys="Match.home_team_id", back_populates="home_team"
    )
    away_matches = relationship(
        "Match", foreign_keys="Match.away_team_id", back_populates="away_team"
    )
    team_stats = relationship("TeamStat", back_populates="team")

    def __repr__(self):
        return f"<Team {self.name}>"


class Player(Base):
    """AFL Player model."""

    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"))
    position = Column(String(50))
    jersey_number = Column(Integer)
    height_cm = Column(Integer)
    weight_kg = Column(Integer)
    date_of_birth = Column(Date)
    debut_year = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="players")
    player_stats = relationship("PlayerStat", back_populates="player")

    def __repr__(self):
        return f"<Player {self.name}>"


class Match(Base):
    """AFL Match model."""

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    match_date = Column(DateTime, nullable=False)
    venue = Column(String(100))
    home_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    away_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    home_score = Column(Integer)
    away_score = Column(Integer)
    attendance = Column(Integer)
    match_status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("season", "round", "home_team_id", "away_team_id"),
    )

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    player_stats = relationship("PlayerStat", back_populates="match")
    team_stats = relationship("TeamStat", back_populates="match")

    def __repr__(self):
        return f"<Match {self.season} R{self.round}: {self.home_team_id} vs {self.away_team_id}>"


class PlayerStat(Base):
    """Player Statistics per match."""

    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True)
    match_id = Column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    disposals = Column(Integer, default=0)
    kicks = Column(Integer, default=0)
    handballs = Column(Integer, default=0)
    marks = Column(Integer, default=0)
    tackles = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    behinds = Column(Integer, default=0)
    hitouts = Column(Integer, default=0)
    clearances = Column(Integer, default=0)
    inside_50s = Column(Integer, default=0)
    contested_possessions = Column(Integer, default=0)
    uncontested_possessions = Column(Integer, default=0)
    clangers = Column(Integer, default=0)
    free_kicks_for = Column(Integer, default=0)
    free_kicks_against = Column(Integer, default=0)
    brownlow_votes = Column(Integer, default=0)
    time_on_ground_pct = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (UniqueConstraint("match_id", "player_id"),)

    # Relationships
    match = relationship("Match", back_populates="player_stats")
    player = relationship("Player", back_populates="player_stats")

    def __repr__(self):
        return f"<PlayerStat Match:{self.match_id} Player:{self.player_id}>"


class TeamStat(Base):
    """Team Statistics per match."""

    __tablename__ = "team_stats"

    id = Column(Integer, primary_key=True)
    match_id = Column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    is_home = Column(Boolean, nullable=False)
    score = Column(Integer, nullable=False)
    inside_50s = Column(Integer)
    clearances = Column(Integer)
    contested_possessions = Column(Integer)
    uncontested_possessions = Column(Integer)
    tackles = Column(Integer)
    marks = Column(Integer)
    hitouts = Column(Integer)
    free_kicks_for = Column(Integer)
    free_kicks_against = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (UniqueConstraint("match_id", "team_id"),)

    # Relationships
    match = relationship("Match", back_populates="team_stats")
    team = relationship("Team", back_populates="team_stats")

    def __repr__(self):
        return f"<TeamStat Match:{self.match_id} Team:{self.team_id}>"


class Conversation(Base):
    """Agent conversation history."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100))
    messages = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Conversation {self.id}>"
