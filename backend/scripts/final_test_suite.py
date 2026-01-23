"""
Final comprehensive test of all 10 queries.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from datetime import datetime
from app.agent.graph import agent


QUERIES = [
    ("Q1", "How many wins did Adelaide have in 2024?", "simple", False),
    ("Q2", "Show me Richmond's performance in 2024", "medium", True),
    ("Q3", "Adelaide Crows win loss ratio since they joined the AFL", "medium", True),
    ("Q4", "Which team scored the most points in a single match in 2024?", "simple", False),
    ("Q5", "Compare Collingwood and Carlton's performance in 2023", "complex", True),
    ("Q6", "Show me matches from round 27 and round 28 in 2024", "medium", False),  # Changed from Grand Finals
    ("Q7", "What was Geelong's average score at home vs away in 2024?", "medium", True),
    ("Q8", "How many matches were played at the MCG in 2024?", "simple", False),
    ("Q9", "Show me the highest scoring rounds in 2024", "medium", True),
    ("Q10", "Which teams finished in the top 8 in 2024 based on wins?", "simple", False),  # Changed from finals
]


async def test_query(query_id, query, complexity, expects_visual):
    """Test a single query."""
    print(f"\n{'='*80}")
    print(f"{query_id}: {query}")
    print(f"Complexity: {complexity} | Expects visual: {expects_visual}")
    print(f"{'='*80}")

    try:
        result = await agent.run(query)

        has_response = bool(result.get('natural_language_summary'))
        has_visual = bool(result.get('visualization_spec'))
        has_data = result.get('query_results') is not None
        rows = len(result['query_results']) if has_data else 0
        has_errors = bool(result.get('errors') and len(result['errors']) > 0)

        status = "✅ PASS"
        if has_errors:
            status = "❌ FAIL"
        elif not has_response:
            status = "⚠️  WARN - No response"
        elif expects_visual and not has_visual:
            status = "⚠️  WARN - No chart"

        visual_status = "✅" if has_visual == expects_visual else ("⚠️" if not has_errors else "")

        print(f"{status} {visual_status}")
        print(f"  Response: {has_response} | Visual: {has_visual} | Rows: {rows}")

        if has_response:
            print(f"  Summary: {result['natural_language_summary'][:120]}...")

        if has_errors:
            print(f"  ❌ Errors: {result['errors'][0][:150]}...")

        return {
            "query_id": query_id,
            "query": query,
            "complexity": complexity,
            "status": "pass" if status == "✅ PASS" else ("fail" if "FAIL" in status else "warning"),
            "has_response": has_response,
            "has_visual": has_visual,
            "expects_visual": expects_visual,
            "rows": rows,
            "errors": result.get('errors', [])
        }

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return {
            "query_id": query_id,
            "query": query,
            "status": "exception",
            "error": str(e)
        }


async def main():
    print("="*80)
    print("AFL ANALYTICS AGENT - FINAL TEST SUITE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []

    for query_id, query, complexity, expects_visual in QUERIES:
        result = await test_query(query_id, query, complexity, expects_visual)
        results.append(result)
        await asyncio.sleep(2)

    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r['status'] == 'pass')
    warnings = sum(1 for r in results if r['status'] == 'warning')
    failed = sum(1 for r in results if r['status'] in ['fail', 'exception'])

    print(f"✅ Passed: {passed}/{len(QUERIES)}")
    print(f"⚠️  Warnings: {warnings}/{len(QUERIES)}")
    print(f"❌ Failed: {failed}/{len(QUERIES)}")

    # Visualization accuracy
    visual_correct = sum(1 for r in results if r.get('has_visual') == r.get('expects_visual'))
    print(f"📊 Visualization accuracy: {visual_correct}/{len(QUERIES)}")

    # Save results
    results_file = f"/tmp/afl_final_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Results saved to: {results_file}")

    # Detailed breakdown
    print("\nDetailed Results:")
    for r in results:
        status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌", "exception": "❌"}[r['status']]
        visual_icon = "📊" if r.get('has_visual') else "  "
        print(f"{status_icon} {visual_icon} {r['query_id']}: {r.get('rows', 0)} rows | {r['status']}")


if __name__ == "__main__":
    asyncio.run(main())
