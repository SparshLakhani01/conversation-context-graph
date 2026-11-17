#!/usr/bin/env python3
"""Evaluate graph retrieval vs. the TF-IDF baseline on a fixed question set.

Each question has:
  - expected: a substring that must appear in a correct answer
    (compared after lowercasing, hyphen->space, whitespace collapse)
  - facts: the fact ids whose stating messages count as supporting
    citations for this question

Metrics (all measured from the actual run, nothing hand-written):
  - correctness: expected substring present in the returned answer
  - citation precision: fraction of returned citations whose message
    states at least one of the question's facts. If an answer returns
    no citations, precision is 1.0 when the answer is correct (nothing
    unsupported was cited) and 0.0 otherwise.

Usage: python -m src.evaluate   (from the project root)
Writes results/eval_results.json and prints a comparison table.
"""
import json
import os
import re

from src.query import BaselineRetriever, GraphQA, Store, _normalize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (question, expected substring, [fact ids])
QUESTIONS = [
    ("Who asked for quarterly billing at Harborview Medical?",
     "Rachel Kim", ["F02"]),
    ("What is the annual value of the Harborview Medical deal?",
     "$96,000", ["F01"]),
    ("When is the Harborview Medical deal expected to close?",
     "December 12", ["F03"]),
    ("Who is the champion for the Harborview Medical deal?",
     "David Osei", ["F04"]),
    ("What is still pending on the Harborview Medical deal?",
     "security review", ["F05"]),
    ("What is Beacon Freight's renewal date?",
     "January 31", ["F11"]),
    ("How much is the Beacon Freight renewal worth per year?",
     "$145,000", ["F10"]),
    ("What expansion is Beacon Freight considering?",
     "analytics module", ["F12"]),
    ("What approval does Beacon Freight's expansion spend need?",
     "board approval", ["F13"]),
    ("How long is the Larkspur Outdoors pilot?",
     "6 week", ["F18"]),
    ("How many users are in the Larkspur Outdoors pilot?",
     "20 users", ["F19"]),
    ("What is the Larkspur Outdoors pilot's success criterion?",
     "30%", ["F20"]),
    ("Who is evaluating the pilot at Larkspur Outdoors?",
     "Ingrid Sorensen", ["F21"]),
    ("When is Larkspur Outdoors' pilot decision due?",
     "January 9", ["F22"]),
    ("Who handles vendor onboarding paperwork at Larkspur Outdoors?",
     "Paul Whitaker", ["F23"]),
    ("Does Ironwood Components have an open deal?",
     "no open deal", ["F27"]),
]


def grade(result, expected, fact_ids, store):
    correct = _normalize(expected) in _normalize(result["answer"])
    supporting = {m["id"] for m in store.messages
                  if set(m["facts"]) & set(fact_ids)}
    cited = [c["message_id"] for c in result["citations"]]
    if not cited:
        precision = 1.0 if correct else 0.0
    else:
        precision = sum(1 for c in cited if c in supporting) / len(cited)
    return correct, precision, cited


def main():
    store = Store()
    graph_qa = GraphQA(store)
    baseline = BaselineRetriever(store)
    rows = []
    for question, expected, fact_ids in QUESTIONS:
        row = {"question": question, "expected": expected}
        for name, engine in (("graph", graph_qa), ("baseline", baseline)):
            result = engine.answer(question)
            correct, precision, cited = grade(result, expected, fact_ids,
                                              store)
            row[name] = {"correct": correct,
                         "citation_precision": round(precision, 3),
                         "citations": cited,
                         "answer": result["answer"]}
        rows.append(row)

    def summary(name):
        acc = sum(r[name]["correct"] for r in rows) / len(rows)
        prec = sum(r[name]["citation_precision"] for r in rows) / len(rows)
        return acc, prec

    print(f"{'question':58s} {'graph':>6s} {'base':>6s}  "
          f"{'graph_prec':>10s} {'base_prec':>9s}")
    print("-" * 100)
    for r in rows:
        q = r["question"][:56]
        print(f"{q:58s} {str(r['graph']['correct']):>6s} "
              f"{str(r['baseline']['correct']):>6s}  "
              f"{r['graph']['citation_precision']:>10.3f} "
              f"{r['baseline']['citation_precision']:>9.3f}")
    print("-" * 100)
    g_acc, g_prec = summary("graph")
    b_acc, b_prec = summary("baseline")
    print(f"accuracy:          graph {g_acc:.3f}  baseline {b_acc:.3f}  "
          f"({len(rows)} questions)")
    print(f"mean citation precision: graph {g_prec:.3f}  "
          f"baseline {b_prec:.3f}")

    out_dir = os.path.join(ROOT, "results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "eval_results.json")
    with open(out, "w") as f:
        json.dump({"n_questions": len(rows),
                   "graph": {"accuracy": g_acc,
                             "mean_citation_precision": g_prec},
                   "baseline": {"accuracy": b_acc,
                                "mean_citation_precision": b_prec},
                   "rows": rows}, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
