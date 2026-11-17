#!/usr/bin/env python3
"""Build the conversation context graph from synthetic messages.

Deterministic, rule-based extraction only: entity mentions are matched
against the registry in data/entities.json (full names and aliases,
case-insensitive). No ML extraction, no external calls.

Graph schema (NetworkX MultiDiGraph, saved as node-link JSON):
  nodes: person | company | deal | message | fact
  edges:
    person -SENT-> message            (sender; attr: timestamp)
    message -TO-> person              (participant; attr: timestamp)
    person -WORKS_AT-> company        (from registry; attr: source="registry")
    company -HAS_DEAL-> deal          (from registry; attr: source="registry")
    message -STATES-> fact            (attr: source_msg, timestamp)
    fact -ABOUT-> person|company|deal (attr: source_msg, timestamp)

Every fact node carries the list of source message ids that state it,
so every stored fact traces back to its source message(s).

Usage: python -m src.ingest   (from the project root)
"""
import json
import os
import re

import networkx as nx
from networkx.readwrite import json_graph

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")


def load_inputs():
    with open(os.path.join(DATA, "messages.json")) as f:
        messages = json.load(f)["messages"]
    with open(os.path.join(DATA, "entities.json")) as f:
        entities = json.load(f)
    return messages, entities


def _alias_patterns(registry_entries):
    """Compile one case-insensitive word-boundary pattern per entity."""
    patterns = {}
    for entry in registry_entries:
        alts = sorted((re.escape(a) for a in entry["aliases"]),
                      key=len, reverse=True)
        patterns[entry["id"]] = re.compile(
            r"\b(" + "|".join(alts) + r")\b", re.IGNORECASE)
    return patterns


def extract_mentions(text, patterns):
    return {eid for eid, pat in patterns.items() if pat.search(text)}


def build_graph(messages, entities):
    g = nx.MultiDiGraph()
    people = {p["id"]: p for p in entities["people"]}
    companies = {c["id"]: c for c in entities["companies"]}
    deals = {d["id"]: d for d in entities["deals"]}

    for p in entities["people"]:
        g.add_node(p["id"], kind="person", label=p["name"],
                   title=p["title"], company=p["company"])
    for c in entities["companies"]:
        g.add_node(c["id"], kind="company", label=c["name"])
    for d in entities["deals"]:
        g.add_node(d["id"], kind="deal", label=d["name"],
                   company=d["company"])
    for fid, fact in entities["facts"].items():
        g.add_node(fid, kind="fact", label=fact["statement"],
                   source_msgs=[])

    name_to_person = {p["name"]: p["id"] for p in entities["people"]}

    person_patterns = _alias_patterns(entities["people"])
    company_patterns = _alias_patterns(entities["companies"])
    deal_patterns = _alias_patterns(entities["deals"])

    for m in messages:
        mid = m["id"]
        g.add_node(mid, kind="message", label=m["subject"],
                   channel=m["channel"], timestamp=m["timestamp"],
                   sender=m["sender"], synthetic=True)
        sender_id = name_to_person.get(m["sender"])
        if sender_id:
            g.add_edge(sender_id, mid, relation="SENT",
                       timestamp=m["timestamp"])
        for participant in m["participants"]:
            pid = name_to_person.get(participant)
            if pid:
                g.add_edge(mid, pid, relation="TO",
                           timestamp=m["timestamp"])
        # deterministic mention extraction over subject + body
        text = f"{m['subject']} {m['body']}"
        for eid in extract_mentions(text, person_patterns):
            if eid != sender_id:
                g.add_edge(mid, eid, relation="MENTIONS",
                           source_msg=mid, timestamp=m["timestamp"])
        for eid in extract_mentions(text, company_patterns):
            g.add_edge(mid, eid, relation="MENTIONS",
                       source_msg=mid, timestamp=m["timestamp"])
        for eid in extract_mentions(text, deal_patterns):
            g.add_edge(mid, eid, relation="MENTIONS",
                       source_msg=mid, timestamp=m["timestamp"])
        # facts stated by this message; every fact keeps its sources
        for fid in m["facts"]:
            g.add_edge(mid, fid, relation="STATES",
                       source_msg=mid, timestamp=m["timestamp"])
            g.nodes[fid]["source_msgs"].append(mid)
            for eid in entities["facts"][fid]["entities"]:
                g.add_edge(fid, eid, relation="ABOUT",
                           source_msg=mid, timestamp=m["timestamp"])

    for p in entities["people"]:
        g.add_edge(p["id"], p["company"], relation="WORKS_AT",
                   source="registry")
    for d in entities["deals"]:
        g.add_edge(d["company"], d["id"], relation="HAS_DEAL",
                   source="registry")
    return g


def main():
    messages, entities = load_inputs()
    g = build_graph(messages, entities)
    out = os.path.join(DATA, "graph.json")
    with open(out, "w") as f:
        json.dump(json_graph.node_link_data(g), f, indent=2)
    kinds = {}
    for _, attrs in g.nodes(data=True):
        kinds[attrs["kind"]] = kinds.get(attrs["kind"], 0) + 1
    print(f"graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print("nodes by kind:", kinds)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
