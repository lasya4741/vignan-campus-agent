"""Live HTTP API validator for the 21 Core Queries across VIGNAN Campus Intelligence."""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

TEST_QUERIES = [
    ("1. Who is the HOD of CSE?", "Who is the HOD of CSE?", None, lambda r: "Dr. S.V. Phani Kumar" in r["answer"] and "Computer Science" in r["answer"]),
    ("2. Who is the HOD of IT?", "Who is the HOD of IT?", None, lambda r: "Dr. Kamepalli Sujatha" in r["answer"] and "Information Technology" in r["answer"]),
    ("3. Where is MHP?", "Where is MHP?", None, lambda r: "MHP / Main Canteen" in r["answer"] and ("near N Block" in r["answer"] or "N Block" in r["answer"])),
    ("4. Where is the main canteen?", "Where is the main canteen?", None, lambda r: "MHP / Main Canteen" in r["answer"]),
    ("5. Where can I get lunch?", "Where can I get lunch?", None, lambda r: "MHP" in r["answer"] or "Canteen" in r["answer"]),
    ("6. Where is Finance?", "Where is Finance?", None, lambda r: "Finance & Accounts Office" in r["answer"] and "A Block" in r["answer"]),
    ("7. Where can I pay my fees?", "Where can I pay my fees?", None, lambda r: "Finance & Accounts Office" in r["answer"] and "A Block" in r["answer"]),
    ("8. Where is IT?", "Where is IT?", None, lambda r: "Information Technology" in r["answer"] and "U Block" in r["answer"]),
    ("9. Where is Balu sir?", "Where is Balu sir?", None, lambda r: "Dr. G Balu Narasimha Rao" in r["answer"] and "NB-409" in r["answer"] and "N Block" in r["answer"]),
    ("10. Who handles placements?", "Who handles placements?", None, lambda r: "Training & Placements" in r["answer"] or "T&P" in r["answer"] or "Balu" in r["answer"]),
    ("11. Where can I Xerox?", "Where can I Xerox?", None, lambda r: "Xerox" in r["answer"]),
    ("12. Which Xerox should I use?", "Which Xerox should I use?", None, lambda r: "Xerox" in r["answer"] and ("Recommended" in r["answer"] or "Facility" in r["answer"])),
    ("13. Where is the Transport Office?", "Where is the Transport Office?", None, lambda r: "Transport Office" in r["answer"] and "Main Gate" in r["answer"]),
    ("14. Who is my counsellor? (no profile)", "Who is my counsellor?", None, lambda r: r.get("requires_clarification") is True and "Year and Section" in r["answer"]),
    ("15. Year 3 Section 8.", "Year 3 Section 8.", None, lambda r: "Section 8" in r["answer"]),
    ("16. How do I get from A Block to MHP?", "How do I get from A Block to MHP?", None, lambda r: r.get("route") is not None and "A Block" in r["route"]["origin"] and "google_maps_url" in r["route"]),
    ("17. How do I get to Finance?", "How do I get to Finance?", None, lambda r: r.get("route") is not None and "Finance" in r["route"]["destination"] and "google_maps_url" in r["route"]),
    ("18. How can I reach the Transport Office?", "How can I reach the Transport Office?", None, lambda r: r.get("route") is not None and "Transport" in r["route"]["destination"] and "google_maps_url" in r["route"]),
    ("19. What does the CSE HOD teach?", "What does the CSE HOD teach?", None, lambda r: "Data Mining" in r["answer"] or "Machine Learning" in r["answer"] or "Deep Learning" in r["answer"]),
    ("20. Write Python code.", "Write Python code.", None, lambda r: "VIGNAN Campus Intelligence Assistant" in r["answer"] and "verified information" in r["answer"]),
    ("21. Explain quantum computing.", "Explain quantum computing.", None, lambda r: "VIGNAN Campus Intelligence Assistant" in r["answer"] and "verified information" in r["answer"]),
]


def run_tests():
    print("=" * 70)
    print("Running Live HTTP Verification for All 21 VIGNAN Core Queries")
    print("=" * 70)

    passed = 0
    failed = 0

    for label, query, user_payload, validator in TEST_QUERIES:
        body = {
            "message": query,
            "session_id": "test_verification_session",
            "user": user_payload or {}
        }
        try:
            resp = requests.post(f"{BASE_URL}/chat", json=body, timeout=5)
            if resp.status_code != 200:
                print(f"[FAIL] {label} -> HTTP {resp.status_code}")
                failed += 1
                continue
            data = resp.json()
            is_valid = validator(data)
            if is_valid:
                print(f"[PASS] {label}")
                passed += 1
            else:
                print(f"[FAIL] {label}")
                print(f"       Query: '{query}'")
                print(f"       Answer: {repr(data.get('answer'))[:200]}")
                print(f"       Route: {data.get('route')}")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {label} -> {e}")
            failed += 1

    print("=" * 70)
    print(f"Result: {passed}/{len(TEST_QUERIES)} Passed, {failed} Failed")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
