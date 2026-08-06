# Complaint Copilot AI — LangGraph Pipeline Diagram

> Auto-generated from `graph.py`.

## Active Pipeline (7 Nodes)

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
	validate_completeness(validate_completeness)
	classify_severity_risk(classify_severity_risk)
	detect_duplicate(detect_duplicate)
	recommend_capa(recommend_capa)
	generate_summary(generate_summary)
	__end__([<p>__end__</p>]):::last
	__start__ --> ingest_document;
	classify_severity_risk --> detect_duplicate;
	detect_duplicate --> recommend_capa;
	extract_entities --> validate_completeness;
	ingest_document --> extract_entities;
	recommend_capa --> generate_summary;
	validate_completeness --> classify_severity_risk;
	generate_summary --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## Node Model Assignments

```
ingest_document
  -> extract_entities        [llama-3.1-8b-instant]
    -> validate_completeness  [llama-3.1-8b-instant]
      -> classify_severity_risk [llama-3.3-70b-versatile]
        -> detect_duplicate    [rule-based SQL]
          -> recommend_capa    [llama-3.3-70b-versatile]
            -> generate_summary [llama-3.1-8b-instant]
              -> END
```
