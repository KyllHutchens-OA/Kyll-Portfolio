"""
Test a single enhanced statistics query to verify implementation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
import json
from app.agent.graph import agent

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def main():
    # Test query that should trigger in-depth mode with trend analysis
    query = "Show me Adelaide's performance over time from 2020 to 2023"

    logger.info(f"Testing query: {query}\n")

    result = await agent.run(query)

    logger.info("=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)

    # Analysis mode
    logger.info(f"\nAnalysis Mode: {result.get('analysis_mode', 'N/A')}")
    logger.info(f"Analysis Types: {result.get('analysis_types', [])}")

    # Statistics
    stats = result.get('statistical_analysis', {})
    logger.info(f"\nStatistics Success: {stats.get('success', False)}")
    logger.info(f"Statistics Mode: {stats.get('mode', 'N/A')}")

    if stats.get('success'):
        logger.info("\nStatistics Computed:")
        for key in stats.keys():
            if key not in ['success', 'mode']:
                logger.info(f"  - {key}: {stats[key].get('success', False)}")

        # Show trend details if available
        if 'trend' in stats and stats['trend'].get('success'):
            trend = stats['trend']
            logger.info(f"\nTrend Analysis Details:")
            logger.info(f"  Summary: {trend.get('summary', 'N/A')}")
            logger.info(f"  Direction: {trend.get('direction', {}).get('classification', 'N/A')}")
            logger.info(f"  Momentum: {trend.get('momentum', {}).get('classification', 'N/A')}")
            logger.info(f"  Confidence: {trend.get('confidence', 'N/A')}")
            logger.info(f"  Sample Size: {trend.get('sample_size', 'N/A')}")

    # Response
    response = result.get('natural_language_summary', '')
    logger.info(f"\nResponse Length: {len(response)} characters")
    logger.info(f"\nResponse:\n{response}")

    # Check if stats are in response
    stats_keywords = ['average', 'trend', 'momentum', 'improving', 'declining',
                      'mean', 'median', 'percent', 'confidence', 'direction']
    has_stats = sum(1 for word in stats_keywords if word in response.lower())

    logger.info(f"\nStatistics keywords found in response: {has_stats}/{len(stats_keywords)}")

    if has_stats >= 3:
        logger.info("✅ Response includes statistical insights!")
    else:
        logger.warning("⚠️  Response may not include statistics")

    # Save full result
    with open('/tmp/enhanced_stats_test_result.json', 'w') as f:
        # Convert pandas DataFrames to strings for JSON serialization
        result_copy = result.copy()
        if 'query_results' in result_copy and result_copy['query_results'] is not None:
            result_copy['query_results'] = result_copy['query_results'].to_dict()

        json.dump(result_copy, f, indent=2, default=str)

    logger.info(f"\nFull result saved to /tmp/enhanced_stats_test_result.json")


if __name__ == "__main__":
    asyncio.run(main())
