#!/usr/bin/env python3
"""FastAPI service for the conversation context graph.

Endpoints:
  GET  /health          -> {"status": "ok"}
  GET  /graph/summary   -> node/edge counts by kind and relation
  POST /query           -> {"question": str, "method": "graph"|"baseline"}
                           returns {"answer", "citations", "method"}

Run: .venv/bin/uvicorn app:app --port 8000   (from the project root)
"""
from collections import Counter

from fastapi import FastAPI
from pydantic import BaseModel

from src.query import BaselineRetriever, GraphQA, Store

app = FastAPI(title="Conversation Context Graph (synthetic demo)")
store = Store()
graph_qa = GraphQA(store)
baseline = BaselineRetriever(store)


class QueryRequest(BaseModel):
    question: str
    method: str = "graph"


@app.get("/health")
def health():
    return {"status": "ok", "synthetic": True}


@app.get("/graph/summary")
def graph_summary():
    g = store.graph
    nodes = Counter(d.get("kind") for _, d in g.nodes(data=True))
    edges = Counter(d.get("relation") for _, _, d in g.edges(data=True))
    return {
        "synthetic": True,
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "nodes_by_kind": dict(nodes),
        "edges_by_relation": dict(edges),
        "messages": len(store.messages),
    }


@app.post("/query")
def query(req: QueryRequest):
    method = req.method if req.method in ("graph", "baseline") else "graph"
    engine = graph_qa if method == "graph" else baseline
    return engine.answer(req.question)
