# Conversation Context Graph

A working prototype that turns a set of business conversations (emails,
meeting notes, Slack-style threads) into a queryable graph where **every
fact traces to its source message**, and compares graph retrieval against
a plain vector-retrieval baseline with a fixed evaluation harness.

## Synthetic-data disclosure

**All data in this project is synthetic.** Every person, company, deal,
date, and dollar figure was invented for this demo. The dataset is
labeled `synthetic: true` in the generator, in the JSON output, and in
the API responses. No real CRM data, no real people, no real companies,
and no affiliation with any CRM vendor. The fictional vendor in the data
is "Meridian", an invented company.

## What it does

1. **Generate** — `data/generate_synthetic.py` writes 60 internally
   consistent messages across 8 people, 5 companies (4 accounts + the
   fictional vendor), and 3 deals, with 30 labeled facts.
2. **Ingest** — `src/ingest.py` extracts entity mentions with
   deterministic registry matching and builds a NetworkX graph:
   person / company / deal / message / fact nodes, with edges carrying
   the source message id and timestamp. Every fact node keeps the list
   of messages that state it.
3. **Query** — `src/query.py` answers questions two ways:
   - `graph`: match entities in the question, walk `fact -ABOUT-> entity`
     edges, rank facts by TF-IDF similarity plus small question-type
     boosts (who/when/how-long/numeric), and return the answer with
     citations (source message id + quote).
   - `baseline`: TF-IDF cosine retrieval over message bodies, top-3,
     no graph. (See the note below on why this is TF-IDF, not dense
     embeddings.)
4. **Evaluate** — `src/evaluate.py` runs a fixed 16-question eval set
   against both methods and reports per-question correctness and
   citation precision.
5. **Serve** — `app.py` exposes the same engine over FastAPI.

## Measured results

From `python -m src.evaluate`, run on 2026-11-16 in this environment
(full per-question table in `results/eval_results.json`):

| Method   | Accuracy (16 questions) | Mean citation precision |
|----------|------------------------:|------------------------:|
| Graph    | 1.000 (16/16)           | 0.958                   |
| Baseline | 0.875 (14/16)           | 0.667                   |

The baseline missed 2 questions (the Harborview annual value and the
Beacon expansion scope: its top-3 retrieved messages did not contain the
expected answer). The graph method answered all 16; its one imperfect
row is "How long is the Larkspur Outdoors pilot?" (citation precision
0.333 — three close-scoring facts were returned, and only one citation
supported the expected fact).

**Read these numbers with care:** the eval set is small (16 questions),
written by the same author as the dataset, and the data is synthetic and
clean. The numbers show the mechanism works on this data; they do not
generalize to real, messy conversation data.

## How to run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Everything in one go: generate, ingest, sample queries, eval
./demo.sh

# Or step by step
.venv/bin/python data/generate_synthetic.py
.venv/bin/python -m src.ingest
.venv/bin/python -m src.query --question "Who asked for quarterly billing at Harborview Medical?"
.venv/bin/python -m src.query --question "Who asked for quarterly billing at Harborview Medical?" --method baseline
.venv/bin/python -m src.evaluate

# API
.venv/bin/uvicorn app:app --port 8000
curl http://127.0.0.1:8000/graph/summary
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "What expansion is Beacon Freight considering?"}'
```

## Architecture

```
data/generate_synthetic.py  -> data/messages.json, data/entities.json
src/ingest.py               -> data/graph.json (NetworkX node-link JSON)
src/query.py                -> GraphQA + BaselineRetriever
src/evaluate.py             -> results/eval_results.json
app.py                      -> FastAPI: /health, /graph/summary, /query
```

Graph schema (106 nodes, 605 edges on the bundled data):

- Nodes: `person` (8), `company` (5), `deal` (3), `fact` (30),
  `message` (60)
- Edges: `SENT`, `TO`, `MENTIONS`, `STATES` (message -> fact),
  `ABOUT` (fact -> entity), `WORKS_AT`, `HAS_DEAL`
- `STATES` and `ABOUT` edges carry `source_msg` + `timestamp`, so any
  answer can be traced back to the exact message it came from.

## Honest limitations

- **Synthetic, clean data.** Real conversations have typos, ambiguous
  names, sarcasm, threads that fork, and facts that get corrected.
  None of that is modeled here.
- **Rule-based extraction.** Entities are matched against a fixed
  registry; there is no NER model, no coreference resolution, and no
  handling of unknown entities.
- **TF-IDF baseline, not dense embeddings.** This environment has no
  sentence-transformers / ChromaDB (no torch), so the "vector" baseline
  is TF-IDF cosine retrieval via scikit-learn, and fact ranking in the
  graph method is also TF-IDF based. Swapping in dense embeddings is a
  one-function change in `BaselineRetriever` / `GraphQA`, but it was
  not run here — nothing in this README claims otherwise.
- **No LLM generation.** Answers are assembled from stored fact
  statements and retrieved quotes, not generated. That is deliberate:
  it keeps every claim traceable to a source.
- **No auth or permissions model.** A real context graph needs
  permission-aware access (who may see which conversation). This
  prototype has none.
- **Small, self-authored eval set.** 16 questions, written against data
  the author also wrote. Directional only.
- **No incremental updates.** Re-ingestion rebuilds the whole graph;
  there is no handling of edited or deleted messages.
- **Single-process, in-memory.** The API loads the graph at startup;
  there is no database.

## Files

| File | Purpose |
|------|---------|
| `data/generate_synthetic.py` | Synthetic dataset generator (60 messages, 30 facts) |
| `data/messages.json` | Generated messages (generated, labeled synthetic) |
| `data/entities.json` | Generated entity/fact registry |
| `data/graph.json` | Built graph, node-link JSON (generated) |
| `src/ingest.py` | Deterministic extraction + graph build |
| `src/query.py` | Graph QA + TF-IDF baseline |
| `src/evaluate.py` | Fixed 16-question eval harness |
| `app.py` | FastAPI service |
| `demo.sh` | End-to-end demo script |
| `requirements.txt` | Pinned dependencies |
| `results/eval_results.json` | Measured eval output (generated) |
