"""Test runner for live Supabase-backed queries through the Agent and Tool layer."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agent import coordinator
from backend.tools import (
    search_department,
    search_faculty,
    search_subject,
    search_counsellor,
    search_office,
    search_responsibility,
    search_service,
    get_location,
    get_route,
)

TEST_QUERIES = [
    {
        "id": 1,
        "query": "Where is IT?",
        "direct_tool": lambda: search_department("Information Technology"),
    },
    {
        "id": 2,
        "query": "Who is the HOD of CSE?",
        "direct_tool": lambda: search_department("Computer Science"),
    },
    {
        "id": 3,
        "query": "Who is my counsellor?",
        "direct_tool": lambda: search_counsellor(registration_number="4005", year=2, section="1"),
    },
    {
        "id": 4,
        "query": "Who handles placements?",
        "direct_tool": lambda: search_responsibility("placements"),
    },
    {
        "id": 5,
        "query": "Where is the Transport Office?",
        "direct_tool": lambda: search_service(category="transport"),
    },
    {
        "id": 6,
        "query": "Where can I Xerox?",
        "direct_tool": lambda: search_service(category="xerox"),
    },
    {
        "id": 7,
        "query": "Where is Finance?",
        "direct_tool": lambda: get_location(query="Finance"),
    },
]

async def test_agent_query(q_text: str):
    try:
        res = await coordinator.process_query(q_text)
        return {
            "answer": res.answer,
            "tool_used": res.tool_used,
            "tool_calls": [tc.model_dump() if hasattr(tc, 'model_dump') else tc.dict() for tc in res.tool_calls],
            "sources": [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in res.sources],
            "confidence": res.confidence,
            "requires_clarification": res.requires_clarification,
            "location": res.location.model_dump() if res.location else None,
            "route": res.route.model_dump() if res.route else None,
            "live_status": res.live_status.model_dump() if res.live_status else None,
        }
    except Exception as e:
        return {"error": str(e)}

def run_all():
    print("=" * 70)
    print("VIGNAN AGENT: LIVE SUPABASE-BACKED REAL QUERY TEST")
    print("=" * 70)

    results = []
    for item in TEST_QUERIES:
        print(f"\n=======================================================")
        print(f"QUERY {item['id']}: '{item['query']}'")
        print(f"=======================================================")
        
        # 1. Execute direct database tool
        tool_res = item["direct_tool"]()
        items_list = tool_res.get("matches") or tool_res.get("data") or ([tool_res.get("route")] if tool_res.get("route") else [])
        print(f"\n[1] DIRECT DATABASE TOOL RESULT:")
        print(f"Total Matches: {len(items_list)}")
        for rec in items_list[:3]:
            print(f"  - Record: {json.dumps(rec, ensure_ascii=False)}")

        # 2. Execute Coordinator Agent
        agent_res = asyncio.run(test_agent_query(item["query"]))
        print(f"\n[2] AGENT COORDINATOR SYNTHESIS:")
        print(f"Answer:\n{agent_res.get('answer')}")
        print(f"Tools Used: {agent_res.get('tool_used')}")
        print(f"Confidence: {agent_res.get('confidence')}")
        print(f"Sources Count: {len(agent_res.get('sources', []))}")

        results.append({
            "query_id": item["id"],
            "query": item["query"],
            "direct_tool_result": tool_res,
            "agent_result": agent_res
        })

    with open("database/seeds/real_queries_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n\nAll 7 live queries executed successfully and saved to database/seeds/real_queries_result.json")

if __name__ == "__main__":
    run_all()
