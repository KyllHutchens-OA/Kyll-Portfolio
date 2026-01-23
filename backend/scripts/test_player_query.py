"""
Test player data availability after schema updates.

Verifies:
- SQL generation includes player tables
- Player queries execute successfully
- Results contain player statistics
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from app.agent.graph import agent

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_player_query():
    """Test a simple player query."""
    query = "How many disposals did Patrick Cripps average in 2024?"

    logger.info("=" * 80)
    logger.info(f"Testing Player Query")
    logger.info(f"Query: {query}")
    logger.info("=" * 80)

    try:
        result = await agent.run(query)

        # Check if query succeeded
        if result.get("success"):
            logger.info("\n✅ Query executed successfully")

            # Check SQL contains player tables
            sql = result.get("sql_query", "")
            if "player" in sql.lower():
                logger.info("✅ SQL references player tables")
                logger.info(f"\nGenerated SQL:\n{sql}\n")
            else:
                logger.warning("⚠️  SQL does not reference player tables")

            # Check for results
            data = result.get("query_results")
            if data is not None and len(data) > 0:
                logger.info(f"✅ Query returned {len(data)} rows")
                logger.info(f"\nResults:\n{data.to_string()}\n")
            else:
                logger.warning("⚠️  Query returned no data")

            # Check response
            response = result.get("natural_language_summary", "")
            if response:
                logger.info(f"✅ Response generated ({len(response)} chars)")
                logger.info(f"\n📝 Response:\n{response}\n")
            else:
                logger.warning("⚠️  No response generated")
        else:
            logger.error(f"❌ Query failed: {result.get('error')}")

        logger.info("=" * 80)
        return result

    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    await test_player_query()


if __name__ == "__main__":
    asyncio.run(main())
