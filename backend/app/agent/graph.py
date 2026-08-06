"""
LangGraph StateGraph Definition — Complaint Copilot AI
Full 7-node pipeline:
  ingest_document -> extract_entities -> validate_completeness
    -> classify_severity_risk -> detect_duplicate -> recommend_capa
    -> generate_summary -> END
"""
import os
from langgraph.graph import StateGraph, END

from app.agent.state import ComplaintState
from app.agent.nodes.ingest import ingest_document_node
from app.agent.nodes.extract_entities import extract_entities_node
from app.agent.nodes.validate_completeness import validate_completeness_node
from app.agent.nodes.classify_risk import classify_risk_node
from app.agent.nodes.detect_duplicate import detect_duplicate_node
from app.agent.nodes.recommend_capa import recommend_capa_node
from app.agent.nodes.generate_summary import generate_summary_node
from app.core.logging import logger


def build_graph():
    """Build and compile the 7-node complaint pipeline StateGraph."""
    workflow = StateGraph(ComplaintState)

    workflow.add_node("ingest_document",       ingest_document_node)
    workflow.add_node("extract_entities",      extract_entities_node)
    workflow.add_node("validate_completeness", validate_completeness_node)
    workflow.add_node("classify_severity_risk", classify_risk_node)
    workflow.add_node("detect_duplicate",      detect_duplicate_node)
    workflow.add_node("recommend_capa",        recommend_capa_node)
    workflow.add_node("generate_summary",      generate_summary_node)

    workflow.set_entry_point("ingest_document")
    workflow.add_edge("ingest_document",       "extract_entities")
    workflow.add_edge("extract_entities",      "validate_completeness")
    workflow.add_edge("validate_completeness", "classify_severity_risk")
    workflow.add_edge("classify_severity_risk","detect_duplicate")
    workflow.add_edge("detect_duplicate",      "recommend_capa")
    workflow.add_edge("recommend_capa",        "generate_summary")
    workflow.add_edge("generate_summary",      END)

    return workflow.compile()


def export_graph_diagram(compiled_graph):
    """Export auto-generated Mermaid diagram to agent_graph_diagram.md."""
    try:
        mermaid_str = compiled_graph.get_graph().draw_mermaid()
        diagram_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "agent_graph_diagram.md")
        )
        content = f"""# Complaint Copilot AI — LangGraph Pipeline Diagram

> Auto-generated from `graph.py`.

## Active Pipeline (7 Nodes)

```mermaid
{mermaid_str}
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
"""
        with open(diagram_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Graph diagram exported to: {diagram_path}")
        return diagram_path
    except Exception as e:
        logger.error(f"Graph diagram export failed: {e}")
        return None


complaint_pipeline = build_graph()
_diagram_path = export_graph_diagram(complaint_pipeline)
