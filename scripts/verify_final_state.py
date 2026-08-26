import urllib.request
import json

def verify():
    print("==================================================")
    print("VIGNAN LIVE SYSTEM FINAL VERIFICATION")
    print("==================================================")

    # 1. Verify /directory?category=services
    with urllib.request.urlopen("http://127.0.0.1:8000/directory?category=services") as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("\n[SERVICES DIRECTORY]")
        for s in data.get("data", []):
            print(f"  * {s.get('name')} | {s.get('description')}")

    # 2. Verify all required test queries
    queries = [
        "Where is the Xerox near Zest?",
        "Where is the Xerox near MHP?",
        "Where is the Xerox near the MHP Zest area?",
        "Where is MHP?",
        "Where is the main canteen?",
        "Where is the finance office?",
        "Who is the counsellor for Year 3 Section 8?",
        "from Main Gate to MHP directions",
        "from Main Gate to Finance Office directions",
        "Who is the HOD of IT?",
        "Where is Balu sir?",
        "Who handles placements?"
    ]

    print("\n[AGENT QUERIES]")
    for q in queries:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/chat",
            data=json.dumps({"message": q}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            print(f"\n--- Q: {q} ---")
            print(f"Tool: {d.get('tool_used')}")
            print(f"Ans:\n{d.get('answer')}")
            if d.get("navigation"):
                print(f"Google Maps URL: {d['navigation'].get('map_url')}")

if __name__ == "__main__":
    verify()
