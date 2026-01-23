-- AFL Analytics Database Schema V2
-- Migration: Enhanced player stats, match details, lineups, and weather data

-- Add additional fields to players table
ALTER TABLE players
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS debut_date DATE;

-- Update players name index to include first/last names
CREATE INDEX IF NOT EXISTS idx_players_first_name ON players(first_name);
CREATE INDEX IF NOT EXISTS idx_players_last_name ON players(last_name);

-- Add enhanced fields to player_stats table
ALTER TABLE player_stats
ADD COLUMN IF NOT EXISTS rebound_50s INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS contested_marks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS marks_inside_50 INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS one_percenters INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS bounces INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS goal_assist INTEGER DEFAULT 0;

-- Add quarter-by-quarter scoring to matches table
ALTER TABLE matches
ADD COLUMN IF NOT EXISTS home_q1_goals INTEGER,
ADD COLUMN IF NOT EXISTS home_q1_behinds INTEGER,
ADD COLUMN IF NOT EXISTS home_q2_goals INTEGER,
ADD COLUMN IF NOT EXISTS home_q2_behinds INTEGER,
ADD COLUMN IF NOT EXISTS home_q3_goals INTEGER,
ADD COLUMN IF NOT EXISTS home_q3_behinds INTEGER,
ADD COLUMN IF NOT EXISTS home_q4_goals INTEGER,
ADD COLUMN IF NOT EXISTS home_q4_behinds INTEGER,
ADD COLUMN IF NOT EXISTS away_q1_goals INTEGER,
ADD COLUMN IF NOT EXISTS away_q1_behinds INTEGER,
ADD COLUMN IF NOT EXISTS away_q2_goals INTEGER,
ADD COLUMN IF NOT EXISTS away_q2_behinds INTEGER,
ADD COLUMN IF NOT EXISTS away_q3_goals INTEGER,
ADD COLUMN IF NOT EXISTS away_q3_behinds INTEGER,
ADD COLUMN IF NOT EXISTS away_q4_goals INTEGER,
ADD COLUMN IF NOT EXISTS away_q4_behinds INTEGER;

-- Match lineups table (which players were selected for each match)
CREATE TABLE IF NOT EXISTS match_lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    jersey_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_match_lineups_match ON match_lineups(match_id);
CREATE INDEX IF NOT EXISTS idx_match_lineups_team ON match_lineups(team_id);
CREATE INDEX IF NOT EXISTS idx_match_lineups_player ON match_lineups(player_id);

-- Match weather table (weather conditions during the match)
CREATE TABLE IF NOT EXISTS match_weather (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE UNIQUE,
    temperature_celsius DECIMAL(4,1),
    apparent_temperature_celsius DECIMAL(4,1),
    rainfall_mm DECIMAL(5,1),
    wind_speed_kmh DECIMAL(4,1),
    wind_direction_degrees INTEGER,
    humidity_pct INTEGER,
    weather_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_match_weather_match ON match_weather(match_id);

-- Trigger for match_weather updated_at
CREATE TRIGGER update_match_weather_updated_at BEFORE UPDATE ON match_weather
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comment to explain weather codes
COMMENT ON COLUMN match_weather.weather_code IS 'WMO Weather interpretation codes: 0=Clear, 1-3=Partly cloudy, 45-48=Fog, 51-67=Rain, 71-77=Snow, 80-99=Showers/Thunderstorms';
