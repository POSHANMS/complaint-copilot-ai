# Complaint Copilot AI — LangGraph Pipeline Diagram

> Auto-generated from `graph.py`. Use this in the demo video to show the real multi-node LangGraph agent structure.

## Step 2: Active Nodes (3-node pipeline)

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	ingest_document(ingest_document)
	extract_entities(extract_entities)
	generate_summary(generate_summary)
	__end__([<p>__end__</p>]):::last
	__start__ --> ingest_document;
	extract_entities --> generate_summary;
	ingest_document --> extract_entities;
	generate_summary --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## Full Pipeline (Steps 2–4)

```
ingest_document
  -> extract_entities        [llama-3.1-8b-instant]
    -> validate_completeness  [llama-3.1-8b-instant]
      -> classify_severity_risk [llama-3.3-70b-versatile]
        -> detect_duplicate    [llama-3.1-8b-instant]
          -> recommend_capa    [llama-3.3-70b-versatile]
            -> generate_summary [llama-3.1-8b-instant]
              -> END
```
