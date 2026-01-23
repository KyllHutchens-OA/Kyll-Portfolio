"""
Test chart improvements - titles, axis labels, and chart type selection.
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


async def test_chart_appearance():
    """Test that charts have proper titles and axis labels."""
    query = "Show me Adelaide's win loss ratio across the time"

    logger.info("="*80)
    logger.info(f"Testing Chart Improvements: {query}")
    logger.info("="*80)

    try:
        result = await agent.run(query)

        # Check visualization
        if result.get('visualization_spec'):
            viz = result['visualization_spec']

            logger.info(f"\n✅ Chart Generated:")
            logger.info(f"  Title: {viz['layout'].get('title', {}).get('text', 'N/A')}")
            logger.info(f"  X-axis: {viz['layout'].get('xaxis', {}).get('title', {}).get('text', 'N/A')}")
            logger.info(f"  Y-axis: {viz['layout'].get('yaxis', {}).get('title', {}).get('text', 'N/A')}")
            logger.info(f"  Chart Type: {viz['data'][0].get('type', 'N/A')}")
            logger.info(f"  Data Points: {len(viz['data'][0].get('x', []))}")

            # Check for improvements
            title = viz['layout'].get('title', {}).get('text', '')
            x_label = viz['layout'].get('xaxis', {}).get('title', {}).get('text', '')
            y_label = viz['layout'].get('yaxis', {}).get('title', {}).get('text', '')

            issues = []
            if query.lower() in title.lower():
                issues.append("❌ Title is still the raw question")
            if x_label == 'season':
                issues.append("❌ X-axis label is not humanized (still 'season')")
            if y_label in ['win_loss_ratio', 'wins', 'losses']:
                issues.append(f"❌ Y-axis label is not humanized (still '{y_label}')")

            if issues:
                logger.warning("\n⚠️  Issues Found:")
                for issue in issues:
                    logger.warning(f"  {issue}")
            else:
                logger.info("\n✅ All improvements working!")
                logger.info("  - Title is descriptive")
                logger.info("  - Axis labels are humanized")

            # Save visualization spec for inspection
            with open('/tmp/test_chart_spec.json', 'w') as f:
                json.dump(viz, f, indent=2)
            logger.info(f"\n📄 Full chart spec saved to /tmp/test_chart_spec.json")

        else:
            logger.error(f"\n❌ No visualization generated")

        return result

    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    await test_chart_appearance()


if __name__ == "__main__":
    asyncio.run(main())
