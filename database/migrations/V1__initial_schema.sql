-- AFL Analytics Database Schema
-- Initial migration: Core tables for teams, players, matches, and statistics

-- Teams table (18 AFL teams)
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    abbreviation VARCHAR(10) NOT NULL UNIQUE,
    stadium VARCHAR(100),
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    founded_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players table
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    position VARCHAR(50),
    jersey_number INTEGER,
    height_cm INTEGER,
    weight_kg INTEGER,
    date_of_birth DATE,
    debut_year INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    season INTEGER NOT NULL,
    round INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    venue VARCHAR(100),
    home_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    home_score INTEGER,
    away_score INTEGER,
    attendance INTEGER,
    match_status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(season, round, home_team_id, away_team_id)
);

-- Player Statistics (per match)
CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    disposals INTEGER DEFAULT 0,
    kicks INTEGER DEFAULT 0,
    handballs INTEGER DEFAULT 0,
    marks INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    behinds INTEGER DEFAULT 0,
    hitouts INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    inside_50s INTEGER DEFAULT 0,
    contested_possessions INTEGER DEFAULT 0,
    uncontested_possessions INTEGER DEFAULT 0,
    clangers INTEGER DEFAULT 0,
    free_kicks_for INTEGER DEFAULT 0,
    free_kicks_against INTEGER DEFAULT 0,
    brownlow_votes INTEGER DEFAULT 0,
    time_on_ground_pct DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, player_id)
);

-- Team Statistics (per match)
CREATE TABLE IF NOT EXISTS team_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    is_home BOOLEAN NOT NULL,
    score INTEGER NOT NULL,
    inside_50s INTEGER,
    clearances INTEGER,
    contested_possessions INTEGER,
    uncontested_possessions INTEGER,
    tackles INTEGER,
    marks INTEGER,
    hitouts INTEGER,
    free_kicks_for INTEGER,
    free_kicks_against INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, team_id)
);

-- Conversations (for agent memory)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    messages JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_active ON players(is_active);

CREATE INDEX IF NOT EXISTS idx_matches_season_round ON matches(season, round);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);

CREATE INDEX IF NOT EXISTS idx_player_stats_match ON player_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_stats(player_id);

CREATE INDEX IF NOT EXISTS idx_team_stats_match ON team_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_stats(team_id);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_stats_updated_at BEFORE UPDATE ON player_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_stats_updated_at BEFORE UPDATE ON team_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
