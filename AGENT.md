# AGENT.md — LangGraph Agent Contract

## Purpose
This file defines the contract for the ComplaintState graph so any node can be modified independently without breaking others.

## State object
See backend/app/agent/state.py — ComplaintState TypedDict. Every node receives the full state and returns a partial update dict (LangGraph merge pattern). Never mutate state in place; always return updates.

## Graph definition
File: backend/app/agent/graph.py

Node order (linear with one conditional branch):
ingest_document
  -> extract_entities
    -> validate_completeness
      -> classify_severity_risk
        -> detect_duplicate
          -> recommend_capa
            -> generate_summary
              -> END

Conditional: if completeness_score < 40%, still proceed through the graph (do not halt), but flag missing_fields prominently in the final state so the UI can show an incomplete-data warning banner. Never block the pipeline on missing data — pharma complaints often arrive incomplete and the system must still produce a best-effort triage.

## Model routing
- llama-3.1-8b-instant: extract_entities, validate_completeness, detect_duplicate, generate_summary (fast, structured extraction tasks)
- llama-3.3-70b-versatile: classify_severity_risk, recommend_capa (higher-stakes reasoning, needs the bigger model)

## Prompting rules
- Every node prompt requests STRICT JSON output with a defined schema. Parse defensively (try/except + fallback to "extraction_failed" flag in state, never crash the graph).
- Every reasoning-producing node (risk, CAPA, duplicate) must return both a machine value (score/label) AND a short human-readable justification string. The justification is what gets shown in the UI — it is not optional.

## Adding a new node (future extension)
1. Create backend/app/agent/nodes/<name>.py with a function (state: ComplaintState) -> dict.
2. Register it in graph.py with add_node + add_edge.
3. Add its output fields to ComplaintState in state.py.
4. Add a corresponding UI card if the output is user-facing.
5. Add an extraction_logs write inside the node.

## Testing
Any node change must be verified against backend/tests/test_graph.py with at least one sample complaint (from sample_complaints/) run through graph.invoke() end-to-end before considering the change done.
