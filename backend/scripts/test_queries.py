"""
Test suite for AFL Analytics Agent - 10 varied queries

Tests queries with varying complexity and visualization requirements.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
import json
from app.agent.graph import agent

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# 10 test queries with varying complexity
TEST_QUERIES = [
    {
        "id": 1,
        "query": "How many wins did Adelaide have in 2024?",
        "complexity": "simple",
        "expects_visual": False,
        "description": "Simple count query"
    },
    {
        "id": 2,
        "query": "Show me Richmond's performance in 2024",
        "complexity": "medium",
        "expects_visual": True,
        "description": "Team performance over season (line chart)"
    },
    {
        "id": 3,
        "query": "Adelaide Crows win loss ratio since they joined the AFL",
        "complexity": "medium",
        "expects_visual": True,
        "description": "Historical win/loss analysis (bar chart)"
    },
    {
        "id": 4,
        "query": "Which team scored the most points in a single match in 2024?",
        "complexity": "simple",
        "expects_visual": False,
        "description": "Max score query"
    },
    {
        "id": 5,
        "query": "Compare Collingwood and Carlton's performance in 2023",
        "complexity": "complex",
        "expects_visual": True,
        "description": "Multi-team comparison (dual line chart)"
    },
    {
        "id": 6,
        "query": "Show me all Grand Final results from 2020 to 2024",
        "complexity": "medium",
        "expects_visual": False,
        "description": "Finals-specific query"
    },
    {
        "id": 7,
        "query": "What was Geelong's average score at home vs away in 2024?",
        "complexity": "medium",
        "expects_visual": True,
        "description": "Home/away comparison (bar chart)"
    },
    {
        "id": 8,
        "query": "How many matches were played at the MCG in 2024?",
        "complexity": "simple",
        "expects_visual": False,
        "description": "Venue-based count"
    },
    {
        "id": 9,
        "query": "Show me the highest scoring rounds in 2024",
        "complexity": "medium",
        "expects_visual": True,
        "description": "Round-based aggregate (bar chart)"
    },
    {
        "id": 10,
        "query": "Which teams made the finals in 2024?",
        "complexity": "simple",
        "expects_visual": False,
        "description": "Finals qualification query"
    }
]


async def test_query(test_case):
    """Run a single test query through the agent."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Test {test_case['id']}: {test_case['description']}")
    logger.info(f"Query: \"{test_case['query']}\"")
    logger.info(f"Complexity: {test_case['complexity']}")
    logger.info(f"Expects visual: {test_case['expects_visual']}")
    logger.info(f"{'='*80}")

    try:
        # Run the query through the agent
        result = await agent.run(test_case['query'])

        # Check for errors
        if result.get('errors'):
            logger.error(f"❌ ERRORS: {result['errors']}")
            return {
                "test_id": test_case['id'],
                "status": "failed",
                "error": result['errors'],
                "has_response": False,
                "has_visual": False
            }

        # Check for response
        has_response = bool(result.get('natural_language_summary'))
        has_visual = bool(result.get('visualization_spec'))

        # Log results
        if has_response:
            logger.info(f"✅ Response: {result['natural_language_summary'][:100]}...")
        else:
            logger.warning(f"⚠️  No response generated")

        if has_visual:
            logger.info(f"✅ Visualization: {result['visualization_spec']['layout'].get('title', 'Chart')}")
        elif test_case['expects_visual']:
            logger.warning(f"⚠️  Expected visualization but none generated")

        # Check SQL
        if result.get('sql_query'):
            logger.info(f"📊 SQL: {result['sql_query'][:80]}...")

        # Check data
        if result.get('query_results') is not None:
            rows = len(result['query_results'])
            logger.info(f"📈 Data: {rows} rows returned")

        # Determine status
        status = "passed"
        if not has_response:
            status = "warning - no response"
        elif test_case['expects_visual'] and not has_visual:
            status = "warning - no visualization"

        return {
            "test_id": test_case['id'],
            "query": test_case['query'],
            "status": status,
            "has_response": has_response,
            "has_visual": has_visual,
            "expects_visual": test_case['expects_visual'],
            "rows_returned": len(result['query_results']) if result.get('query_results') is not None else 0,
            "sql_query": result.get('sql_query', '')
        }

    except Exception as e:
        logger.error(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "test_id": test_case['id'],
            "status": "exception",
            "error": str(e),
            "has_response": False,
            "has_visual": False
        }


async def main():
    """Run all test queries."""
    logger.info("\n" + "="*80)
    logger.info("AFL ANALYTICS AGENT - QUERY TEST SUITE")
    logger.info("="*80)
    logger.info(f"Running {len(TEST_QUERIES)} test queries...")

    results = []

    for test_case in TEST_QUERIES:
        result = await test_query(test_case)
        results.append(result)

        # Small delay between queries
        await asyncio.sleep(1)

    # Summary report
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for r in results if r['status'] == 'passed')
    warnings = sum(1 for r in results if 'warning' in r['status'])
    failed = sum(1 for r in results if r['status'] in ['failed', 'exception'])

    logger.info(f"✅ Passed: {passed}/{len(TEST_QUERIES)}")
    logger.info(f"⚠️  Warnings: {warnings}/{len(TEST_QUERIES)}")
    logger.info(f"❌ Failed: {failed}/{len(TEST_QUERIES)}")

    # Detailed results
    logger.info("\nDetailed Results:")
    for r in results:
        status_icon = "✅" if r['status'] == 'passed' else "⚠️" if 'warning' in r['status'] else "❌"
        logger.info(f"{status_icon} Test {r['test_id']}: {r['status']}")
        if r.get('error'):
            logger.info(f"   Error: {r['error']}")
        logger.info(f"   Response: {r['has_response']}, Visual: {r['has_visual']} (expected: {r.get('expects_visual', 'N/A')})")

    # Save results to JSON
    with open('/tmp/afl_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\n📄 Full results saved to: /tmp/afl_test_results.json")

    return results


if __name__ == "__main__":
    asyncio.run(main())
