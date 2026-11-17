#!/usr/bin/env python3
"""Answer questions over the conversation context graph, with citations.

Two methods, same interface:

  graph    -- match entities in the question against the registry, walk
              fact -ABOUT-> entity edges, rank facts by keyword overlap
              with the question, and return the top facts with citations
              (source message id + short quote from that message).
  baseline -- plain vector retrieval: TF-IDF over message bodies, top-3
              chunks, no graph. Citations are the retrieved messages.

  NOTE ON THE BASELINE: this environment has no sentence-transformers /
  ChromaDB (no torch), so the baseline is TF-IDF cosine retrieval via
  scikit-learn, not dense embeddings. That is stated honestly here and
  in the README; swapping in dense embeddings is a one-function change
  in BaselineRetriever.

Every answer carries citations. A citation is a dict:
  {"message_id": "MSG-012", "quote": "<first 140 chars of the body>"}

Usage:
  python -m src.query --question "Who asked for quarterly billing at Harborview Medical?"
  python -m src.query --question "..." --method baseline
"""
import argparse
import json
import os
import re

import networkx as nx
from networkx.readwrite import json_graph
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "who", "what", "when",
    "where", "which", "does", "do", "did", "how", "much", "many", "long",
    "by", "for", "at", "on", "in", "of", "to", "and", "or", "it", "its",
    "their", "there", "with", "have", "has", "had", "be", "been", "per",
}

QUOTE_LEN = 140


def _normalize(text):
    return re.sub(r"\s+", " ", text.lower().replace("-", " ")).strip()


def _tokens(text):
    return [t for t in re.findall(r"[a-z0-9%$]+", _normalize(text))
            if t not in STOPWORDS]


class Store:
    """Loads messages, registry, and the built graph."""

    def __init__(self):
        with open(os.path.join(DATA, "messages.json")) as f:
            self.messages = json.load(f)["messages"]
        with open(os.path.join(DATA, "entities.json")) as f:
            self.entities = json.load(f)
        with open(os.path.join(DATA, "graph.json")) as f:
            self.graph = json_graph.node_link_graph(json.load(f))
        self.by_id = {m["id"]: m for m in self.messages}
        self._patterns = {}
        for group in ("people", "companies", "deals"):
            for entry in self.entities[group]:
                alts = sorted((re.escape(a) for a in entry["aliases"]),
                              key=len, reverse=True)
                self._patterns[entry["id"]] = re.compile(
                    r"\b(" + "|".join(alts) + r")\b", re.IGNORECASE)

    def match_entities(self, text):
        return {eid for eid, pat in self._patterns.items()
                if pat.search(text)}

    def quote(self, message_id):
        body = self.by_id[message_id]["body"]
        q = re.sub(r"\s+", " ", body).strip()
        return q[:QUOTE_LEN] + ("..." if len(q) > QUOTE_LEN else "")

    def citation(self, message_id):
        return {"message_id": message_id, "quote": self.quote(message_id)}


MONTHS = {"january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"}
DURATIONS = {"week", "weeks", "day", "days", "month", "months",
             "year", "years"}
# Small lexical expansions: question words mapped to the wording facts
# use ("decision" in a question vs "decide" in the fact, etc.).
EXPANSIONS = {"decision": "decide", "value": "worth"}


class GraphQA:
    """Entity-filtered fact retrieval with lexical + question-type ranking.

    1. Match entities in the question against the registry.
    2. Candidate facts = facts with an ABOUT edge to a matched entity.
    3. Rank by TF-IDF cosine between the question and the fact
       statement, plus small deterministic boosts for question types
       (who -> person facts, when -> date facts, how long -> duration
       facts, how much/value -> numeric facts, "open deal" -> the
       no-open-deal fact). Only facts scoring above a threshold are
       returned, so same-entity but irrelevant facts are excluded.
    """

    def __init__(self, store, top_k=3, threshold=0.05, margin=0.15):
        self.store = store
        self.top_k = top_k
        self.threshold = threshold
        self.margin = margin
        g = store.graph
        self._fact_ids = [n for n, d in g.nodes(data=True)
                          if d.get("kind") == "fact"]
        statements = [g.nodes[f]["label"] for f in self._fact_ids]
        self._vectorizer = TfidfVectorizer()
        self._matrix = self._vectorizer.fit_transform(statements)
        self._about = {}
        for fid in self._fact_ids:
            self._about[fid] = {t for _, t, d in g.out_edges(fid, data=True)
                                if d.get("relation") == "ABOUT"}

    def _boost(self, question, fid, statement):
        q = _normalize(question)
        qset = set(_tokens(question))
        stoks = set(_tokens(statement))
        boost = 0.0
        if "who" in qset and any(
                self.store.graph.nodes[e].get("kind") == "person"
                for e in self._about[fid]):
            boost += 0.30
        if "when" in qset and stoks & MONTHS:
            boost += 0.30
        if "how" in qset and "long" in qset and stoks & DURATIONS:
            boost += 0.30
        if qset & {"much", "many", "worth", "value"} and any(
                ch.isdigit() for ch in statement):
            boost += 0.30
        if "open deal" in q and "no open deal" in _normalize(statement):
            boost += 0.50
        return boost

    def answer(self, question):
        g = self.store.graph
        matched = self.store.match_entities(question)
        if not matched:
            return {"answer": "I could not match the question to any person, "
                              "company, or deal in the conversation graph.",
                    "citations": [], "method": "graph"}
        qtext = question + " " + " ".join(
            EXPANSIONS[t] for t in _tokens(question) if t in EXPANSIONS)
        qvec = self._vectorizer.transform([qtext])
        sims = cosine_similarity(qvec, self._matrix)[0]
        scored = []
        for i, fid in enumerate(self._fact_ids):
            if not (self._about[fid] & matched):
                continue
            attrs = g.nodes[fid]
            score = float(sims[i]) + self._boost(question, fid,
                                                 attrs["label"])
            latest = max(self.store.by_id[mid]["timestamp"]
                         for mid in attrs["source_msgs"])
            scored.append((score, latest, fid, attrs))
        scored.sort(key=lambda r: (r[0], r[1]), reverse=True)
        # Keep facts above the threshold AND within a margin of the top
        # score: same-entity facts that are clearly less relevant than
        # the best match are excluded, so citations stay on-topic.
        top = []
        if scored:
            best = scored[0][0]
            top = [r for r in scored
                   if r[0] > self.threshold and r[0] >= best - self.margin]
            top = top[: self.top_k] or scored[:1]
        statements = [attrs["label"] for _, _, _, attrs in top]
        answer = "Based on the conversation graph: " + " ".join(statements)
        citations, seen = [], set()
        for _, _, _, attrs in top:
            # cite the most recent source message for each fact
            mid = max(attrs["source_msgs"],
                      key=lambda m: self.store.by_id[m]["timestamp"])
            if mid not in seen:
                seen.add(mid)
                citations.append(self.store.citation(mid))
        return {"answer": answer, "citations": citations, "method": "graph"}


class BaselineRetriever:
    """TF-IDF cosine retrieval over message bodies (no graph)."""

    def __init__(self, store, top_k=3):
        self.store = store
        self.top_k = top_k
        self._docs = [f"{m['subject']} {m['body']}"
                      for m in store.messages]
        self._vectorizer = TfidfVectorizer()
        self._matrix = self._vectorizer.fit_transform(self._docs)

    def answer(self, question):
        q = self._vectorizer.transform([question])
        sims = cosine_similarity(q, self._matrix)[0]
        ranked = sims.argsort()[::-1][: self.top_k]
        hits = [(self.store.messages[i], float(sims[i]))
                for i in ranked if sims[i] > 0]
        if not hits:
            return {"answer": "No relevant messages retrieved.",
                    "citations": [], "method": "baseline"}
        excerpts = [self.store.quote(m["id"]) for m, _ in hits]
        answer = "Retrieved messages: " + " | ".join(excerpts)
        citations = [self.store.citation(m["id"]) for m, _ in hits]
        return {"answer": answer, "citations": citations,
                "method": "baseline"}


def answer_question(question, method="graph", store=None):
    store = store or Store()
    if method == "baseline":
        return BaselineRetriever(store).answer(question)
    return GraphQA(store).answer(question)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--method", choices=["graph", "baseline"],
                    default="graph")
    args = ap.parse_args()
    result = answer_question(args.question, args.method)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
