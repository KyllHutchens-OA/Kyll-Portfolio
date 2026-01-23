"""
Test script for AFL Analytics Agent.

Tests the agent with simple queries.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent import agent


async def test_agent():
    """Test the agent with a simple query."""
    print("=" * 80)
    print("AFL Analytics Agent - Test")
    print("=" * 80)

    # Test query
    query = "Who won the 2025 grand final?"

    print(f"\nQuery: {query}")
    print("\nProcessing...\n")

    try:
        result = await agent.run(query)

        print("=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(f"\nIntent: {result.get('intent')}")
        print(f"Entities: {result.get('entities')}")
        print(f"\nSQL Query:")
        print(result.get('sql_query', 'N/A'))
        print(f"\nRows returned: {len(result.get('query_results', [])) if result.get('query_results') is not None else 0}")
        print(f"\nResponse:")
        print(result.get('natural_language_summary', 'N/A'))
        print(f"\nConfidence: {result.get('confidence', 0.0):.2f}")

        if result.get('errors'):
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent())
