"""
Test temporal query improvements.
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


async def test_temporal_query():
    """Test the exact query the user had issues with."""
    query = "Show me adelaides win loss ratio across the time"

    logger.info("="*80)
    logger.info(f"Testing Temporal Query: {query}")
    logger.info("="*80)

    try:
        result = await agent.run(query)

        # Extract key info
        intent = result.get('intent')
        has_visual = bool(result.get('visualization_spec'))
        rows = len(result['query_results']) if result.get('query_results') is not None else 0
        sql = result.get('sql_query', '')

        logger.info(f"\n✅ Results:")
        logger.info(f"  Intent: {intent}")
        logger.info(f"  Rows returned: {rows}")
        logger.info(f"  Has visualization: {has_visual}")

        if rows > 0:
            logger.info(f"\n📊 Data Preview:")
            logger.info(result['query_results'].head(10).to_string())

        if rows == 1:
            logger.error(f"\n❌ FAILED: Only 1 row returned (aggregate instead of time-series)")
        elif rows < 3:
            logger.warning(f"\n⚠️  WARNING: Only {rows} rows (may not be enough for good chart)")
        else:
            logger.info(f"\n✅ SUCCESS: {rows} rows returned (good for time-series chart)")

        logger.info(f"\n📝 SQL Generated:")
        logger.info(f"  {sql[:200]}...")

        if result.get('natural_language_summary'):
            logger.info(f"\n💬 Response:")
            logger.info(f"  {result['natural_language_summary'][:200]}...")

        if result.get('errors'):
            logger.error(f"\n❌ Errors: {result['errors']}")

        return {
            "success": rows >= 3,
            "intent": str(intent),
            "rows": rows,
            "has_visual": has_visual
        }

    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_multiple_temporal_queries():
    """Test various temporal query phrasings."""
    queries = [
        "Show me adelaides win loss ratio across the time",
        "Adelaide's performance over time",
        "Richmond win rate year by year",
        "How has Geelong's scoring changed since 2010?",
        "Show me Collingwood's historical win trend",
    ]

    logger.info("\n" + "="*80)
    logger.info("TESTING MULTIPLE TEMPORAL QUERIES")
    logger.info("="*80)

    results = []

    for i, query in enumerate(queries, 1):
        logger.info(f"\n[{i}/{len(queries)}] Testing: {query}")

        try:
            result = await agent.run(query)
            rows = len(result['query_results']) if result.get('query_results') is not None else 0
            intent = result.get('intent')

            status = "✅ PASS" if rows >= 3 else "❌ FAIL" if rows == 1 else "⚠️  WARN"
            logger.info(f"{status} - Intent: {intent}, Rows: {rows}")

            results.append({
                "query": query,
                "intent": str(intent),
                "rows": rows,
                "success": rows >= 3
            })

        except Exception as e:
            logger.error(f"❌ EXCEPTION: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })

        await asyncio.sleep(2)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)

    passed = sum(1 for r in results if r.get('success'))
    logger.info(f"✅ Passed: {passed}/{len(queries)}")

    for r in results:
        status = "✅" if r.get('success') else "❌"
        logger.info(f"{status} {r['query']}: {r.get('rows', 'error')} rows")

    return results


async def main():
    # Test the specific failing query first
    result = await test_temporal_query()

    # Then test variations
    if result.get('success'):
        logger.info("\n\n🎉 Primary test passed! Testing variations...")
        await test_multiple_temporal_queries()
    else:
        logger.error("\n\n❌ Primary test failed. Fix needed before testing variations.")


if __name__ == "__main__":
    asyncio.run(main())
