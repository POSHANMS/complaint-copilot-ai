# AIVOA — AI-Powered Customer Complaint Management System
## MASTER BUILD PROMPT (System Design + Context Engineering)

> Paste this entire document into Antigravity as the first prompt. This is the single source of truth for the build. Do not deviate from the architecture unless a genuine blocker forces it — if it does, stop and report back before improvising.

---

## 0. MISSION BRIEFING (read this first)

You are building a **production-grade demo** of an AI Complaint Intake system for a pharmaceutical QMS (Quality Management System). The reviewer will watch the first 10-15 seconds of a demo video and form an instant opinion. Your job is not just "make it work" — it's **make it look like a funded startup's internal tool**, while the underlying AI pipeline is genuinely a multi-step LangGraph agent (not a single API call wearing a trenchcoat).

Two things must both be true simultaneously:
1. **First-impression wow**: split-screen UI, smooth extraction animation, form fields populating live, chat assistant responding — polished, restrained, professional (NOT flashy/childish).
2. **Real engineering underneath**: a genuine multi-node LangGraph state machine, real FastAPI endpoints, real Postgres persistence, real reasoning visible in the risk/completeness output — because you will be asked to explain and extend this live in an interview.

Optimize for **both** at once. Never sacrifice one for the other.

---

## 1. MANDATORY TECH STACK (non-negotiable)

| Layer | Technology |
|---|---|
| Frontend | React (Vite) + Redux Toolkit |
| Backend | Python + FastAPI |
| AI Agent Framework | LangGraph |
| LLM | Groq API — `gemma2-9b-it` primary, `llama-3.3-70b-versatile` for heavier reasoning nodes |
| Database | PostgreSQL |
| Font | Google Inter (self-hosted or Google Fonts CDN) |
| Realtime feel | Simulated streaming via SSE or polling during extraction (not literally required, but must *feel* live) |

---

## 2. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT (React)                          │
│                                                                     │
│  ┌───────────────────────┐      ┌──────────────────────────┐   │
│  │  Log Complaint Form    │      │  AI Complaint Intake       │   │
│  │  (left panel)          │◄────►│  Assistant (right panel)   │   │
│  │  - Redux-controlled    │      │  - Upload/paste zone       │   │
│  │  - field-level loading │      │  - Extraction progress bar │   │
│  │    skeletons           │      │  - Chat interface          │   │
│  └───────────────────────┘      └──────────────────────────┘   │
│              │                              │                      │
│              └──────────────┬───────────────┘                      │
│                              ▼                                      │
│                     Redux store (single source of truth)            │
│                              │                                      │
│                     Axios/Fetch API client                          │
└──────────────────────────────┼─────────────────────────────────────┘
                                 │  REST + SSE
┌────────────────────────────────▼─────────────────────────────────┐
│                       BACKEND (FastAPI)                            │
│                                                                       │
│  /api/complaints/extract   → triggers LangGraph pipeline (async)     │
│  /api/complaints/           → CRUD                                    │
│  /api/complaints/{id}/chat  → chat-with-complaint endpoint            │
│  /api/complaints/{id}/risk  → risk classification                     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    LANGGRAPH PIPELINE                          │  │
│  │                                                                   │  │
│  │  [ingest_document] → [extract_entities] → [validate_completeness]│  │
│  │         → [classify_severity_risk] → [detect_duplicate]          │  │
│  │         → [recommend_capa] → [generate_summary] → [END]          │  │
│  │                                                                   │  │
│  │  Each node = separate function, separate prompt, separate         │  │
│  │  Groq call where needed. State object passed & mutated at each    │  │
│  │  step. Graph is exportable as a diagram (LangGraph .get_graph()   │  │
│  │  .draw_mermaid()) — SHOW THIS in the demo video.                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────┬───────────────────────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   PostgreSQL      │
                        │  complaints        │
                        │  extraction_logs    │
                        │  chat_messages       │
                        │  audit_trail          │
                        └───────────────────┘
```

---

## 3. THE LANGGRAPH AGENT — NODE-BY-NODE DESIGN

This is the technical heart of the project. Build it as a real `StateGraph`, not a linear script pretending to be one.

**Shared State Object (`ComplaintState`, a TypedDict/Pydantic model):**
```python
class ComplaintState(TypedDict):
    raw_input: str                 # extracted text from PDF/DOCX/TXT/EML or pasted text
    input_type: str                # "pdf" | "docx" | "txt" | "eml" | "text"
    extracted_fields: dict         # all form fields
    missing_fields: list[str]
    completeness_score: float
    severity: str                  # Critical / Major / Minor
    priority: str                  # High / Medium / Low
    risk_score: float
    risk_reasoning: str
    is_duplicate: bool
    duplicate_match_id: str | None
    capa_recommendation: str
    summary: str
    chat_history: list[dict]
    errors: list[str]
```

**Nodes:**

1. **`ingest_document`** — parse uploaded file (pdfplumber/python-docx/plain text/email parser) → raw text. No AI call, pure parsing. Production-grade OCR not required (per brief) — plain text extraction is fine.
2. **`extract_entities`** (Groq `gemma2-9b-it`) — structured extraction prompt, forced JSON output, populates: complaint source, customer name, product name, strength/grade, batch/lot number, manufacturing date, expiry date, quantity affected, complaint type, complaint date, detailed description.
3. **`validate_completeness`** — rule-based + LLM hybrid: checks which required fields are empty/low-confidence, computes a completeness score (0-100%), lists missing fields. *(Bonus feature #1: Complaint Completeness Checker)*
4. **`classify_severity_risk`** (Groq `llama-3.3-70b-versatile` — heavier reasoning) — assigns Severity (Critical/Major/Minor) and Priority, with a **visible reasoning trail** (2-3 sentence justification), not just a label. *(Bonus feature #2: AI Risk Classification)*
5. **`detect_duplicate`** — embeds the complaint description (or does keyword/batch-number matching against existing DB rows) and flags likely duplicates with a similarity score. *(Bonus feature #3: Duplicate Complaint Detection)*
6. **`recommend_capa`** (Groq) — given the complaint type + severity, generates a draft Corrective and Preventive Action (CAPA) recommendation using real QMS terminology (root cause categories: Material, Method, Machine, Man, Environment). *(Bonus feature #4: CAPA Recommendation + Root Cause Recommendation combined)*
7. **`generate_summary`** — 2-3 sentence executive summary of the whole complaint for the AI Copilot panel. *(Bonus feature #5: Complaint Summary)*
8. **`END`** — final state persisted to Postgres, streamed back to frontend field-by-field (not as one giant JSON dump — see UX section).

> Build ALL bonus features. This is the overkill directive — do not skip any of them. Each one is a LangGraph node, cheap to add once the graph pattern exists, and each is worth outsized "wow" in review.

**Chat node (separate small graph or single node):** `chat_with_complaint` — takes chat_history + the full extracted complaint state as context, answers free-text questions ("what's the risk here and why?", "has this batch had complaints before?").

---

## 4. BACKEND FILE STRUCTURE (FastAPI)

```
backend/
├── app/
│   ├── main.py                      # FastAPI app entrypoint, CORS, router mounting
│   ├── core/
│   │   ├── config.py                 # env vars, Groq keys, DB URL (pydantic-settings)
│   │   └── logging.py
│   ├── db/
│   │   ├── database.py               # SQLAlchemy engine/session
│   │   ├── models.py                 # Complaint, ExtractionLog, ChatMessage, AuditTrail
│   │   └── schemas.py                # Pydantic request/response models
│   ├── api/
│   │   ├── routes_complaints.py      # CRUD + list + get
│   │   ├── routes_extraction.py      # POST /extract (file/text upload → triggers graph)
│   │   ├── routes_chat.py            # POST /complaints/{id}/chat
│   │   └── routes_health.py
│   ├── agent/
│   │   ├── graph.py                  # StateGraph definition, node wiring, compile()
│   │   ├── state.py                  # ComplaintState schema
│   │   ├── nodes/
│   │   │   ├── ingest.py
│   │   │   ├── extract_entities.py
│   │   │   ├── validate_completeness.py
│   │   │   ├── classify_risk.py
│   │   │   ├── detect_duplicate.py
│   │   │   ├── recommend_capa.py
│   │   │   ├── generate_summary.py
│   │   │   └── chat_node.py
│   │   ├── prompts/
│   │   │   ├── extraction_prompt.py
│   │   │   ├── risk_prompt.py
│   │   │   ├── capa_prompt.py
│   │   │   └── chat_prompt.py
│   │   └── llm_client.py             # Groq client wrapper, model selection per node
│   ├── services/
│   │   ├── document_parser.py        # pdf/docx/eml/txt → text
│   │   └── similarity.py             # duplicate detection helper
│   └── utils/
│       └── streaming.py              # SSE helper for field-by-field response
├── tests/
│   └── test_graph.py                 # at least a smoke test on the graph
├── sample_complaints/                 # your own realistic pharma complaint PDFs/emails
├── requirements.txt
├── .env.example
└── Dockerfile
```

---

## 5. FRONTEND FILE STRUCTURE (React + Redux)

```
frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── store/
│   │   ├── store.js
│   │   └── slices/
│   │       ├── complaintSlice.js       # form fields, extraction status per field
│   │       ├── chatSlice.js
│   │       └── uiSlice.js               # loading states, toasts
│   ├── api/
│   │   └── client.js                    # axios instance + endpoints
│   ├── components/
│   │   ├── ComplaintForm/
│   │   │   ├── ComplaintForm.jsx
│   │   │   ├── FieldGroup.jsx            # section headers: Origin, Product, Complaint, Assessment
│   │   │   ├── SkeletonField.jsx         # "Awaiting AI extraction..." shimmer state
│   │   │   └── SeverityBadge.jsx
│   │   ├── AICopilot/
│   │   │   ├── AICopilotPanel.jsx
│   │   │   ├── UploadDropzone.jsx
│   │   │   ├── ExtractionProgressBar.jsx
│   │   │   ├── ChatMessageList.jsx
│   │   │   └── ChatInput.jsx
│   │   ├── RiskPanel/
│   │   │   ├── RiskScoreCard.jsx          # visible reasoning, not just a label
│   │   │   ├── CompletenessChecklist.jsx
│   │   │   ├── DuplicateWarningBanner.jsx
│   │   │   └── CAPARecommendationCard.jsx
│   │   └── shared/
│   │       ├── Button.jsx
│   │       └── ProgressBar.jsx
│   ├── hooks/
│   │   ├── useExtractionStream.js        # SSE/polling hook
│   │   └── useChat.js
│   ├── styles/
│   │   ├── theme.css                      # Inter font, color tokens, spacing scale
│   │   └── globals.css
│   └── assets/
├── index.html
├── vite.config.js
├── package.json
└── .env.example
```

---

## 6. DATABASE SCHEMA (Postgres)

```sql
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_source TEXT,
    customer_name TEXT,
    product_name TEXT,
    product_strength_grade TEXT,
    batch_lot_number TEXT,
    manufacturing_date DATE,
    expiry_date DATE,
    quantity_affected TEXT,
    complaint_type TEXT,
    complaint_date DATE,
    detailed_description TEXT,
    initial_severity TEXT,        -- Critical / Major / Minor
    priority TEXT,                 -- High / Medium / Low
    risk_score FLOAT,
    risk_reasoning TEXT,
    completeness_score FLOAT,
    missing_fields TEXT[],
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_match_id UUID REFERENCES complaints(id),
    capa_recommendation TEXT,
    ai_summary TEXT,
    status TEXT DEFAULT 'Pending Triage',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE extraction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id),
    node_name TEXT,               -- which LangGraph node
    input_snapshot JSONB,
    output_snapshot JSONB,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id),
    role TEXT,                     -- 'user' | 'assistant'
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

`extraction_logs` is a small addition that pays off huge in the interview: you can literally show "here's every node's input/output for this run" — instant credibility.

---

## 7. THE "WOW IN 1-2 SECONDS" UX SPEC

The reviewer's eye should register, in order:
1. **Clean split-screen layout, generous whitespace, Inter font** — signals "designed," not "hacked together."
2. **A visible extraction progress bar with % and a status line** ("Analyzing document content and extracting key details...") — signals real async work happening, not instant fake magic.
3. **Form fields populate one-by-one, not all at once** — stagger each field's transition from "Awaiting AI extraction..." skeleton to filled value by 150-300ms. This single detail is disproportionately impressive and easy to build (just sequence the Redux dispatches).
4. **Severity/Priority render as colored badges** (Critical = red, Major = amber, Minor = gray) the instant they're set — visual hierarchy at a glance.
5. **AI Copilot chat panel proactively sends the first message** ("I've extracted this as a [Major] severity complaint for [Product]. Want me to explain the risk reasoning?") instead of sitting idle — signals agentic behavior, not just a form-filler.
6. **Duplicate/CAPA/Risk cards slide in below the form**, each with a one-line "why" — reasoning visible, not a black box.

Do **not** overdesign with gradients, excessive animation, or gimmicks — pharma/enterprise tone is clean, restrained, high-contrast, confident. Think Linear/Notion/Vercel dashboard aesthetics, not a hackathon toy.

---

## 8. DEMO VIDEO STRUCTURE (for your own build reference)

1. **0:00-0:15** — Drop a complaint PDF in, form fills live, chat responds. No narration yet, just the wow.
2. **0:15-1:30** — Narrate: "Here's the LangGraph pipeline" → show the printed/rendered graph diagram → walk each node briefly.
3. **1:30-3:00** — Frontend code: Redux slice, skeleton-to-filled field transition, SSE hook.
4. **3:00-5:00** — Backend code: FastAPI route → graph.invoke() → each node's prompt → Postgres write.
5. **5:00-6:30** — Bonus features: Completeness checker, Risk reasoning, Duplicate detection, CAPA — show each output on screen with the reasoning text visible.
6. **6:30-7:30** — End-to-end recap: PDF in → form + risk assessment out, in under a minute.

Two video submission requested — split as (a) working demo walkthrough, (b) full code explanation walkthrough, matching structure above.

---

## 9. CONTEXT ENGINEERING FILES

Create these two files at the project root. They are what you (or any AI agent, including a future Antigravity session) reads first before touching code — they encode the "how we build this" rules so nothing drifts.

### `SKILL.md` (project root)

```markdown
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
```

### `AGENT.md` (project root)

```markdown
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
- gemma2-9b-it: extract_entities, validate_completeness, detect_duplicate, generate_summary (fast, cheap, structured extraction tasks)
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
```

---

## 10. BUILD ORDER (given your tight deadline)

Given the 36-48hr window, build in this exact sequence — each step should leave you with something demoable even if you have to stop early:

1. **Scaffolding** — repo structure, FastAPI hello-world, React hello-world, Postgres connection, Groq API key working with one test call.
2. **Linear graph, 3 nodes only** — ingest → extract_entities → generate_summary. Get PDF-in, JSON-out working end-to-end through the API, no UI yet.
3. **Basic UI wired to real data** — form + skeleton states + Redux, connected to the 3-node backend. This is your minimum viable demo — **stop here and confirm it works before adding more.**
4. **Add remaining 4 nodes** (completeness, risk, duplicate, CAPA) one at a time, each immediately wired to a UI card.
5. **Polish pass** — staggered field animation, colored severity badges, chat proactive first message, Inter font, spacing.
6. **Record demo videos, write README, push to GitHub.**

Do not attempt to build all 7 nodes before touching the UI — you'll run out of time with nothing demoable. Step 3 is your safety checkpoint.

---

## 11. FINAL REMINDER TO THE BUILDING AGENT

You are optimizing for two audiences at once: a reviewer skimming for 90 seconds, and an interviewer who will ask you to explain or extend this live. Every shortcut you take must survive both. If you're ever unsure whether to cut a corner, don't — flag it and ask instead of silently simplifying, because silent simplification is exactly what turns a "best of the best" build into a generic one.
