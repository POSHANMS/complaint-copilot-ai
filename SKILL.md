# SKILL: AIVOA Complaint System Build Standards

## When to use this
Reference this file before writing ANY backend, frontend, or agent code in this repo.

## Non-negotiables
- Stack is fixed: React+Redux / FastAPI / LangGraph / Groq / Postgres / Inter font. Never substitute.
- Every LangGraph node is a separate file under agent/nodes/. No monolithic single-prompt "extraction."
- Every AI output that affects severity/risk/CAPA MUST include a visible reasoning string, not just a label.
- Frontend form fields must animate from skeleton -> filled state individually, never all at once.
- All Groq calls go through agent/llm_client.py — never call the Groq SDK directly from a node file.
- Every node writes an entry to extraction_logs for auditability.
- No hardcoded API keys. All secrets via .env, loaded through core/config.py.

## Code style
- Backend: type-hinted Python, Pydantic models for all request/response bodies, async def for all route handlers.
- Frontend: functional components only, Redux Toolkit slices (no raw Redux boilerplate), no inline styles except dynamic values.
- Commit style: one logical unit per commit (e.g. "feat: add extract_entities node", "feat: skeleton-to-filled field animation"). Never one giant commit.

## Definition of done for a feature
1. Works end-to-end (upload -> graph -> DB -> UI).
2. Has a visible reasoning/explanation surfaced in UI, not just buried in logs.
3. You (Poshan) can explain every line if asked in interview -- if you can't, re-read and simplify before moving on.
