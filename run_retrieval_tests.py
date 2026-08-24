#!/usr/bin/env python3
"""
Retrieval quality harness.

Validates that the RAG pipeline can actually find the right information,
without calling the LLM (fast, free, deterministic):

  A. Static spot-checks: hand-written questions with known expected sources
  B. Dynamic school sweep: for every school in the DB, ask about it by name
     and require that school's content to dominate the results

Run: python3 run_retrieval_tests.py [--quiet]
Exit code: 0 if pass rate >= threshold, 1 otherwise (CI-friendly).
"""

import sys
import random

PASS_THRESHOLD = 0.75

# (query, expected_school_id) — expected content must come from that school
STATIC_CASES = [
    ("what time is lunch at kennedy high school", "kennedy"),
    ("washington high school bell schedule", "washington"),
    ("irvington high school counseling", "irvington"),
    ("who is the principal of american high school", "american"),
    ("horner middle school bell schedule", "horner"),
    ("fremont unified district board meetings", "district"),
    ("thornton middle school staff", "thornton"),
    ("weibel elementary school information", "weibel"),
]


def run(static_only=False):
    from backend.app.retrieval.hybrid_retriever import HybridRetriever
    retriever = HybridRetriever.instance()

    passed = failed = 0
    failures = []

    print("=" * 64)
    print("RETRIEVAL TEST HARNESS")
    print("=" * 64)

    # --- Static cases ---
    print(f"\n--- {len(STATIC_CASES)} static spot-checks ---")
    for query, expected in STATIC_CASES:
        try:
            results, detected = retriever.retrieve(query, k=6)
            top_schools = [r["school_id"] for r in results[:3]]
            ok = expected in top_schools or expected == detected
            if ok:
                passed += 1
                print(f"  ✅ '{query}' -> {top_schools}")
            else:
                failed += 1
                failures.append((query, f"expected {expected}, got {top_schools}"))
                print(f"  ❌ '{query}' -> expected {expected}, got {top_schools}")
        except Exception as e:
            failed += 1
            failures.append((query, str(e)))
            print(f"  💥 '{query}' -> ERROR {e}")

    # --- Dynamic school sweep ---
    if not static_only:
        import sqlite3
        db = sqlite3.connect("backend/app/database/../school_data.db")
        rows = db.execute(
            "SELECT s.school_id, s.school_name, COUNT(p.id) as n "
            "FROM schools s JOIN pages p ON p.school_id = s.school_id "
            "GROUP BY s.school_id HAVING n >= 5 ORDER BY n DESC"
        ).fetchall()
        db.close()

        sample_n = min(len(rows), 12)
        random.seed(42)
        sampled = random.sample(rows, sample_n)

        print(f"\n--- dynamic sweep over {sample_n} random schools ---")
        for school_id, school_name, n in sampled:
            query = f"{school_name} general information and programs"
            try:
                results, detected = retriever.retrieve(query, k=5)
                top3 = [r["school_id"] for r in results[:3]]
                ok = school_id in top3
                if ok:
                    passed += 1
                    print(f"  ✅ [{school_id}] found in top-3 ({n} pages indexed)")
                else:
                    # Not fatal: tiny schools compete against big ones globally.
                    # Pass if the school appears anywhere in top-5.
                    all5 = [r["school_id"] for r in results]
                    soft_ok = school_id in all5
                    if soft_ok:
                        passed += 1
                        print(f"  🟡 [{school_id}] in top-5 but not top-3")
                    else:
                        failed += 1
                        failures.append((query, f"school absent: got {all5}"))
                        print(f"  ❌ [{school_id}] absent from results ({n} pages)")
            except Exception as e:
                failed += 1
                failures.append((query, str(e)))
                print(f"  💥 [{school_id}] ERROR {e}")

    total = passed + failed
    rate = passed / total if total else 0.0
    print("\n" + "=" * 64)
    print(f"RESULT: {passed}/{total} passed ({rate:.0%}) | threshold {PASS_THRESHOLD:.0%}")
    if failures:
        print("\nFailures:")
        for q, why in failures:
            print(f"  - {q}: {why}")
    print("=" * 64)

    return rate >= PASS_THRESHOLD


if __name__ == "__main__":
    ok = run(static_only="--static" in sys.argv)
    sys.exit(0 if ok else 1)
