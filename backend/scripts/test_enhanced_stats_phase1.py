"""
Test Enhanced Statistics System - Phase 1 & 2 Implementation

Tests:
1. Mode detection (summary vs in-depth)
2. Dynamic analysis types
3. All three statistics methods (trends, comparison, rankings)
4. Statistics integration in response
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


async def test_query(query: str, expected_mode: str):
    """Test a single query and verify mode detection."""
    logger.info("=" * 80)
    logger.info(f"Query: {query}")
    logger.info(f"Expected mode: {expected_mode}")
    logger.info("=" * 80)

    try:
        result = await agent.run(query)

        # Check mode detection
        actual_mode = result.get('analysis_mode')
        analysis_types = result.get('analysis_types', [])

        logger.info(f"\n✅ Analysis Mode: {actual_mode}")
        logger.info(f"✅ Analysis Types: {analysis_types}")

        if actual_mode != expected_mode:
            logger.warning(f"⚠️  Mode mismatch! Expected {expected_mode}, got {actual_mode}")

        # Check statistics
        stats = result.get('statistical_analysis', {})
        if stats.get('success'):
            logger.info(f"\n📊 Statistics Computed:")
            for analysis_type in analysis_types:
                if analysis_type in stats:
                    logger.info(f"  ✓ {analysis_type}: {stats[analysis_type].get('success', False)}")
        else:
            logger.warning("⚠️  No statistics computed")

        # Check response includes stats
        response = result.get('natural_language_summary', '')
        logger.info(f"\n📝 Response Preview:")
        logger.info(response[:300] + "..." if len(response) > 300 else response)

        # Verify stats are in response (check for keywords)
        has_stats = any(word in response.lower() for word in [
            'average', 'trend', 'momentum', 'improving', 'declining',
            'mean', 'median', 'percent', 'confidence'
        ])

        if has_stats:
            logger.info(f"\n✅ Response includes statistical insights!")
        else:
            logger.warning(f"\n⚠️  Response may not include statistics")

        return result

    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests."""

    test_cases = [
        # Summary mode tests
        ("Who won the 2024 grand final?", "summary"),
        ("What was the score in round 1 2024?", "summary"),

        # In-depth mode tests - temporal
        ("Show me Adelaide's win loss ratio over time", "in_depth"),
        ("How has Carlton's performance changed across time?", "in_depth"),

        # In-depth mode tests - team analysis
        ("Tell me about Richmond", "in_depth"),
        ("Analyze Geelong's season", "in_depth"),

        # In-depth mode tests - comparison (when we have multiple entities)
        ("Compare Adelaide and Brisbane Lions", "in_depth"),
    ]

    for query, expected_mode in test_cases:
        await test_query(query, expected_mode)
        await asyncio.sleep(1)  # Brief pause between queries

    logger.info("\n" + "=" * 80)
    logger.info("All tests complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
