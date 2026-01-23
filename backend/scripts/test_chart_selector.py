"""
Test ChartSelector integration in the agent workflow.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from app.agent.graph import agent

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_trend_query():
    """Test a trend query that should create a line chart."""
    query = "Show me Richmond's wins over time from 2018 to 2023"

    logger.info("=" * 80)
    logger.info(f"Testing ChartSelector with Trend Query")
    logger.info(f"Query: {query}")
    logger.info("=" * 80)

    try:
        result = await agent.run(query)

        # Check if visualization was created
        viz_spec = result.get("visualization_spec")
        if viz_spec:
            logger.info(f"\n✅ Visualization created")
            logger.info(f"Chart type: {viz_spec.get('type', 'unknown')}")

            # Check data traces
            if 'data' in viz_spec and len(viz_spec['data']) > 0:
                first_trace = viz_spec['data'][0]
                logger.info(f"Chart mode: {first_trace.get('mode', 'unknown')}")
                logger.info(f"X-axis: {first_trace.get('name', 'N/A')}")

            # Check layout
            if 'layout' in viz_spec:
                layout = viz_spec['layout']
                logger.info(f"Title: {layout.get('title', {}).get('text', 'N/A')}")
        else:
            logger.warning("⚠️  No visualization created")

        # Check response
        response = result.get("natural_language_summary", "")
        if response:
            logger.info(f"\n✅ Response generated ({len(response)} chars)")
            logger.info(f"\n📝 Response preview:\n{response[:300]}...")
        else:
            logger.warning("⚠️  No response generated")

        logger.info("\n" + "=" * 80)
        return result

    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    await test_trend_query()


if __name__ == "__main__":
    asyncio.run(main())
