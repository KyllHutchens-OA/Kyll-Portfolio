"""
Batch test queries - runs synchronously and logs to file.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
import json
from datetime import datetime

# Set up logging to file AND console
log_file = f"/tmp/afl_query_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from app.agent.graph import agent


QUERIES = [
    ("Q1", "How many wins did Adelaide have in 2024?", False),
    ("Q2", "Show me Richmond's performance in 2024", True),
    ("Q3", "Adelaide Crows win loss ratio in 2024", True),
]


async def test_query(query_id, query, expects_visual):
    """Test a single query."""
    logger.info(f"\n{'='*80}")
    logger.info(f"{query_id}: {query}")
    logger.info(f"Expects visual: {expects_visual}")
    logger.info(f"{'='*80}")

    try:
        result = await agent.run(query)

        # Extract key info
        has_response = bool(result.get('natural_language_summary'))
        has_visual = bool(result.get('visualization_spec'))
        has_data = result.get('query_results') is not None
        rows = len(result['query_results']) if has_data else 0

        logger.info(f"✅ Response: {has_response}")
        logger.info(f"✅ Visual: {has_visual}")
        logger.info(f"✅ Data: {rows} rows")

        if has_response:
            logger.info(f"📝 Summary: {result['natural_language_summary'][:150]}...")

        if result.get('errors'):
            logger.error(f"❌ Errors: {result['errors']}")

        return {
            "query_id": query_id,
            "query": query,
            "success": has_response,
            "has_visual": has_visual,
            "expects_visual": expects_visual,
            "rows": rows,
            "errors": result.get('errors', [])
        }

    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "query_id": query_id,
            "query": query,
            "success": False,
            "error": str(e)
        }


async def main():
    logger.info("="*80)
    logger.info("AFL ANALYTICS AGENT - BATCH QUERY TEST")
    logger.info(f"Log file: {log_file}")
    logger.info("="*80)

    results = []

    for query_id, query, expects_visual in QUERIES:
        result = await test_query(query_id, query, expects_visual)
        results.append(result)
        await asyncio.sleep(2)  # Short delay between queries

    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)

    for r in results:
        status = "✅ PASS" if r.get('success') else "❌ FAIL"
        visual_status = "✅" if r.get('has_visual') == r.get('expects_visual') else "⚠️"
        logger.info(f"{status} {visual_status} {r['query_id']}: {r.get('rows', 0)} rows")

    # Save to JSON
    results_file = "/tmp/afl_batch_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\n📄 Results saved to: {results_file}")
    logger.info(f"📄 Log saved to: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
