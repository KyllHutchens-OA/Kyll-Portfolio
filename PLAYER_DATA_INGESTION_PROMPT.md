# Player Data Ingestion Task

## Context
I'm building an AFL Analytics Agent and need to ingest player statistics data into the database. The CSV files are already available at `/Users/kyllhutchens/Code/AFL App/data/afl-data-analysis/data/` but the `players` and `player_stats` tables are currently empty.

## Goal
Ingest 13,206 player performance CSV files (~682,000 rows) into the PostgreSQL database to enable player-level analytics.

## Database Connection
- Database: PostgreSQL via Supabase
- Connection details in: `/Users/kyllhutchens/Code/AFL App/backend/.env`
- Models defined in: `/Users/kyllhutchens/Code/AFL App/backend/app/data/models.py`

## Data Location
Player CSV files are at:
```
/Users/kyllhutchens/Code/AFL App/data/afl-data-analysis/data/player_performance_stats/
```

Format: `lastname_firstname_DDMMYYYY_performance_details.csv`

Each file contains per-match statistics with columns like:
- kicks, marks, handballs, disposals, goals, behinds
- tackles, hitouts, clearances, inside_50s, rebound_50s
- contested_possessions, uncontested_possessions, contested_marks
- marks_inside_50, one_percenters, clangers
- free_kicks_for, free_kicks_against
- brownlow_votes, goal_assist, bounces, time_on_ground_pct

## Database Schema
Refer to `/Users/kyllhutchens/Code/AFL App/backend/app/data/models.py` for:
- `Player` model (id, name, team_id, position, height, weight, debut_year)
- `PlayerStat` model (22 statistical fields per match)

## Task Requirements

1. **Create an ingestion script** at `/Users/kyllhutchens/Code/AFL App/backend/app/data/ingestion/player_ingester.py` that:
   - Reads all CSV files in the player_performance_stats directory
   - Extracts player name from filename
   - Creates Player records (if not exists)
   - Creates PlayerStat records for each match
   - Links to existing Match records via match_date and teams
   - Uses batch inserts for performance (1000 rows at a time)
   - Handles duplicates gracefully
   - Shows progress (e.g., "Processed 1000/13206 files")

2. **Data Validation**:
   - Ensure disposals = kicks + handballs
   - Skip rows with invalid/missing dates
   - Log warnings for data quality issues but don't crash

3. **Performance**:
   - Use SQLAlchemy bulk_insert_mappings for speed
   - Commit in batches of 1000
   - Estimated time: 1-2 hours for full ingestion

4. **Error Handling**:
   - Continue on individual file errors (log and skip)
   - Resume capability if interrupted
   - Final summary: "Ingested X players, Y stats, Z errors"

## Test the Script
After creating the script, run it:
```bash
cd /Users/kyllhutchens/Code/AFL App/backend
source venv/bin/activate
python app/data/ingestion/player_ingester.py
```

## Success Criteria
- Players table populated with 5,700+ player records
- PlayerStats table populated with 682,000+ rows
- Can query: "SELECT COUNT(*) FROM player_stats" and get ~682K
- Can query player statistics by name and date

## Notes
- This is a one-time bulk load (no need for incremental updates yet)
- Focus on correctness over speed (but use batching for reasonable performance)
- Match linking: Use match_date + team names to find match_id
- Some players may have played for multiple teams across their career

## Example Query After Ingestion
After successful ingestion, this query should work:
```sql
SELECT
    p.name,
    ps.match_id,
    ps.disposals,
    ps.goals,
    ps.tackles
FROM player_stats ps
JOIN players p ON ps.player_id = p.id
WHERE p.name ILIKE '%Cripps%'
ORDER BY ps.match_id DESC
LIMIT 10;
```

Please implement this ingestion script and run it to completion, providing progress updates and a final summary.
