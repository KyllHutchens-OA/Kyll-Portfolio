"""
Check what seasons have player data available.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.tools import DatabaseTool

# Check all seasons with player data
result = DatabaseTool.query_database("""
    SELECT DISTINCT m.season, COUNT(DISTINCT ps.player_id) as player_count, COUNT(*) as total_stats
    FROM player_stats ps
    INNER JOIN matches m ON ps.match_id = m.id
    GROUP BY m.season
    ORDER BY m.season DESC
""")

if result["success"]:
    print("\nSeasons with player statistics:")
    print(result["data"])
    print(f"\nTotal seasons: {len(result['data'])}")
else:
    print(f"Error: {result['error']}")

print("\n" + "=" * 80)

# Check 2024 specifically
result = DatabaseTool.query_database("""
    SELECT COUNT(DISTINCT ps.player_id) as players_with_2024_data,
           COUNT(*) as total_2024_stats
    FROM player_stats ps
    INNER JOIN matches m ON ps.match_id = m.id
    WHERE m.season = 2024
""")

if result["success"]:
    print("\n2024 Season Player Data:")
    print(result["data"])
else:
    print(f"Error: {result['error']}")

print("\n" + "=" * 80)

# Check 2025 specifically
result = DatabaseTool.query_database("""
    SELECT COUNT(DISTINCT ps.player_id) as players_with_2025_data,
           COUNT(*) as total_2025_stats
    FROM player_stats ps
    INNER JOIN matches m ON ps.match_id = m.id
    WHERE m.season = 2025
""")

if result["success"]:
    print("\n2025 Season Player Data:")
    print(result["data"])
else:
    print(f"Error: {result['error']}")
