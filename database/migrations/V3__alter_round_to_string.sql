-- Migration V3: Change round column from INTEGER to VARCHAR to support finals rounds
-- Reason: Finals rounds are named (e.g., "Qualifying Final", "Grand Final") not numbered

ALTER TABLE matches
ALTER COLUMN round TYPE VARCHAR(50);
