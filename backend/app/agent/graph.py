"""
LangGraph StateGraph Definition — Complaint Copilot AI
Step 2: 3-node linear pipeline: ingest_document -> extract_entities -> generate_summary
Remaining 4 nodes (completeness, risk, duplicate, CAPA) added in Step 4.

After compiling, the Mermaid diagram of the graph is exported to
backend/agent_graph_diagram.md for demo video use.
"""
import os
from langgraph.graph import StateGraph, END

from app.agent.state import ComplaintState
from app.agent.nodes.ingest import ingest_document_node
from app.agent.nodes.extract_entities import extract_entities_node
from app.agent.nodes.generate_summary import generate_summary_node
from app.core.logging import logger


def build_graph():
    """Build and compile the 3-node complaint pipeline StateGraph."""
    workflow = StateGraph(ComplaintState)

    # Register nodes
    workflow.add_node("ingest_document", ingest_document_node)
    workflow.add_node("extract_entities", extract_entities_node)
    workflow.add_node("generate_summary", generate_summary_node)

    # Linear edges
    workflow.set_entry_point("ingest_document")
    workflow.add_edge("ingest_document", "extract_entities")
    workflow.add_edge("extract_entities", "generate_summary")
    workflow.add_edge("generate_summary", END)

    compiled = workflow.compile()
    return compiled


def export_graph_diagram(compiled_graph):
    """Export the Mermaid diagram of the compiled graph to agent_graph_diagram.md."""
    try:
        mermaid_str = compiled_graph.get_graph().draw_mermaid()
        diagram_path = os.path.join(os.path.dirname(__file__), "..", "..", "agent_graph_diagram.md")
        diagram_path = os.path.normpath(diagram_path)

        content = f"""# Complaint Copilot AI — LangGraph Pipeline Diagram

> Auto-generated from `graph.py`. Use this in the demo video to show the real multi-node LangGraph agent structure.

## Step 2: Active Nodes (3-node pipeline)

```mermaid
{mermaid_str}
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
"""
        with open(diagram_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Graph diagram exported to: {diagram_path}")
        return diagram_path
    except Exception as e:
        logger.error(f"Graph diagram export failed: {e}")
        return None


# Compile on import — this is the object imported by routes
complaint_pipeline = build_graph()

# Export diagram automatically when graph is compiled
_diagram_path = export_graph_diagram(complaint_pipeline)
