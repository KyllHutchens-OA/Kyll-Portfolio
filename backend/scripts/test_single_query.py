"""
Test a single query to debug issues.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from app.agent.graph import agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    query = "Adelaide Crows win loss ratio since they joined the AFL"

    logger.info(f"Testing query: {query}")

    try:
        result = await agent.run(query)

        logger.info("\n" + "="*80)
        logger.info("RESULT:")
        logger.info("="*80)

        # Print key fields
        logger.info(f"Intent: {result.get('intent')}")
        logger.info(f"Entities: {result.get('entities')}")
        logger.info(f"SQL Query: {result.get('sql_query', 'None')}")
        logger.info(f"Rows returned: {len(result.get('query_results', []))} rows")
        logger.info(f"Response: {result.get('natural_language_summary', 'None')}")
        logger.info(f"Has visualization: {result.get('visualization_spec') is not None}")
        logger.info(f"Errors: {result.get('errors', [])}")

        if result.get('query_results') is not None and len(result['query_results']) > 0:
            logger.info(f"\nFirst few rows:")
            logger.info(result['query_results'].head())

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
