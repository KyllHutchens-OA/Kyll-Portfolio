"""Check if 2024 matches exist in database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.tools import DatabaseTool

# Check 2024 matches
result = DatabaseTool.query_database("""
    SELECT season, COUNT(*) as match_count
    FROM matches
    WHERE season IN (2023, 2024, 2025)
    GROUP BY season
    ORDER BY season
""")

print("Matches by season:")
print(result["data"])

print("\n" + "=" * 80)

# Check a specific 2024 match
result = DatabaseTool.query_database("""
    SELECT id, season, round, home_team_id, away_team_id, match_date
    FROM matches
    WHERE season = 2024
    LIMIT 5
""")

print("\nSample 2024 matches:")
print(result["data"])
