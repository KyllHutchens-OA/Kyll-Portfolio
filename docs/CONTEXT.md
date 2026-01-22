# AFL Analytics Agent - Current State

## Last Updated
2026-01-22 by Claude Code

## Project Status
🟡 Week 1: Foundation - Database and scraper implemented, awaiting Supabase connection

## What's Working
- ✅ Project structure initialized with all directories
- ✅ Git repository created and pushed to GitHub (https://github.com/KyllHutchens-OA/AFLChat.git)
- ✅ Database schema created (teams, players, matches, player_stats, team_stats, conversations)
- ✅ SQLAlchemy models with relationships implemented
- ✅ AFL data scraper implemented using Squiggle API
- ✅ Database initialization scripts created
- ✅ Python virtual environment set up with core dependencies

## Currently Working On
- 🔨 Verifying Supabase database connection
- 🔨 Testing database initialization
- 🔨 Running first data ingestion test

## Next Steps
1. **Fix Supabase connection**:
   - Verify Supabase project is created and running
   - Update `.env` file with correct connection string from Supabase dashboard
   - Test database connection with `python scripts/init_db.py`

2. **Test scraper with 2024 season**:
   - Run: `python scripts/ingest_data.py`
   - Verify data is correctly inserted into database

3. **Ingest full historical data (2020-2024)**:
   - Scraper configured to fetch 5 years of AFL data
   - Expected ~1,000+ matches, ~45,000+ player stat records

4. **Build Flask API with health check endpoint**

5. **Create LangGraph agent core (Week 2)**

## Known Issues
- ❌ Supabase host cannot be resolved: `db.igdcvgxbglzhhfczznhw.supabase.co`
  - **Cause**: Either Supabase project not set up, or incorrect connection string
  - **Fix**: Verify Supabase project exists and update `.env` with correct `DB_STRING`

- ⚠️ Python 3.14 compatibility:
  - Updated dependencies to use psycopg3 instead of psycopg2
  - Using latest pandas/numpy versions for Python 3.14 support

## Important Decisions Made
- Using **Squiggle API** instead of scraping AFL Tables (cleaner JSON data, easier to parse)
- Using **psycopg3** (modern PostgreSQL adapter) instead of psycopg2
- 5 years of historical data (2020-2024) for MVP
- No authentication in MVP (can add in Phase 2)
- LangGraph for agent framework (stateful workflows, streaming support)

## Critical Files Created This Session

### Configuration
- `/backend/app/config.py` - Configuration management with environment variables
- `/.env.example` - Template for environment variables
- `/.gitignore` - Git ignore rules for Python/Node projects

### Database
- `/database/migrations/V1__initial_schema.sql` - SQL schema with all tables and indexes
- `/backend/app/data/database.py` - SQLAlchemy engine and session management
- `/backend/app/data/models.py` - Team, Player, Match, PlayerStat, TeamStat, Conversation models

### Data Ingestion
- `/backend/app/data/ingestion/afl_tables.py` - Squiggle API scraper for AFL data
- `/scripts/init_db.py` - Initialize database schema
- `/scripts/ingest_data.py` - Run data ingestion pipeline

### Documentation
- `/README.md` - Project overview and quick start guide
- `/docs/CONTEXT.md` - This file (current project state)

## Database Schema

```sql
teams (18 AFL teams with colors, stadiums, founded years)
players (active and historical players with team relationships)
matches (2020-2024 seasons with scores, venues, attendance)
player_stats (per-match statistics: disposals, goals, tackles, etc.)
team_stats (per-match team aggregates: score, inside_50s, clearances)
conversations (agent chat history in JSONB format)
```

## How to Resume

### Starting Next Session
```bash
# 1. Navigate to project
cd "/Users/kyllhutchens/Code/AFL App"

# 2. Activate virtual environment
source backend/venv/bin/activate

# 3. Check git status
git status
git log --oneline -5

# 4. Read this file for current state
cat docs/CONTEXT.md
```

### Current Blocker
**Fix Supabase connection before proceeding:**

1. Go to https://supabase.com/dashboard
2. Create new project or verify existing project
3. Project Settings → Database → Connection string (Transaction pooler)
4. Update `.env`:
   ```bash
   DB_STRING='postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres'
   ```
5. Test connection:
   ```bash
   python scripts/init_db.py
   ```

### After Supabase Fixed
```bash
# Initialize database (creates all tables)
python scripts/init_db.py

# Test scraper with 2024 season
python scripts/ingest_data.py

# Verify data
# (Connect to Supabase dashboard and check tables)
```

## Tech Stack Summary

**Backend**: Flask + LangGraph + SQLAlchemy + psycopg3
**Database**: Supabase (PostgreSQL)
**Data Source**: Squiggle API (https://api.squiggle.com.au)
**Python**: 3.14 (latest)

## Git Repository
- **URL**: https://github.com/KyllHutchens-OA/AFLChat.git
- **Branch**: main
- **Last Commit**: feat: initialize AFL Sports Analytics Agent project

## Next Session Priorities
1. Fix Supabase connection
2. Test database initialization
3. Run first data ingestion (2024 season)
4. Verify data quality
5. Start Flask API implementation
