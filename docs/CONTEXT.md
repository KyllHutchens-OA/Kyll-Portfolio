# AFL Analytics Agent - Current State

## Last Updated
2026-01-22 17:35 by Claude Code

## Project Status
🟢 Week 1: COMPLETE - Foundation, database, and 5 years of AFL data ingested!

## What's Working
- ✅ Project structure initialized with all directories
- ✅ Git repository created and pushed to GitHub (https://github.com/KyllHutchens-OA/AFLChat.git)
- ✅ Database schema created (teams, players, matches, player_stats, team_stats, conversations)
- ✅ SQLAlchemy models with relationships implemented
- ✅ AFL data scraper implemented using Squiggle API
- ✅ Database initialization scripts created
- ✅ Python virtual environment set up with core dependencies

## Currently Working On
- ✅ Week 1 complete! Ready to start Week 2 (LangGraph agent implementation)

## Next Steps
1. **Build Flask API with health check endpoint**
2. **Create LangGraph agent core (Week 2)**:
   - Set up LangGraph workflow graph (UNDERSTAND → PLAN → EXECUTE → RESPOND)
   - Implement query_database tool with SQL validation
   - Build text-to-SQL generator using GPT-4
   - Test with simple queries ("Who won the 2024 grand final?")

3. **Add visualization and streaming (Week 3)**
4. **Deploy and polish (Week 4)**

## Known Issues
- None! All Week 1 blockers resolved.

## Issues Resolved
- ✅ Supabase connection fixed (using pooler endpoint)
- ✅ Python 3.14 compatibility achieved (psycopg3, pandas 2.2+)
- ✅ Squiggle API User-Agent header added
- ✅ Prepared statements disabled for Supabase pooler compatibility

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

### Verify Data Ingestion
```bash
# Check ingested data
python scripts/check_data.py

# Should show:
# - 18 teams
# - 1,008 matches (2020-2024)
# - 2,016 team stats records
```

### Ready for Week 2
Week 1 foundation is complete! Next session can begin LangGraph agent implementation.

## Tech Stack Summary

**Backend**: Flask + LangGraph + SQLAlchemy + psycopg3
**Database**: Supabase (PostgreSQL)
**Data Source**: Squiggle API (https://api.squiggle.com.au)
**Python**: 3.14 (latest)

## Git Repository
- **URL**: https://github.com/KyllHutchens-OA/AFLChat.git
- **Branch**: main
- **Last Commit**: feat(data): fix Supabase connection and complete AFL data ingestion
- **Status**: Week 1 complete, 1,008 matches ingested

## Next Session Priorities (Week 2)
1. Set up Flask API with health check endpoint
2. Install and configure LangGraph
3. Create agent workflow graph (UNDERSTAND → PLAN → EXECUTE → RESPOND)
4. Implement query_database tool with SQL validation
5. Build text-to-SQL generator using GPT-4
6. Test with simple queries
