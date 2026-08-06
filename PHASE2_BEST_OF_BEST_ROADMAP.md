# Complaint Copilot AI — Phase 2: Best-of-the-Best Roadmap

> You have the full 7-node pipeline working. This document takes it from "assignment complete" to "flagship portfolio piece." Work through phases in order — each is independently valuable, so even if you stop partway, you're strictly better off than before.

---

## PHASE 5 — REAL STREAMING (kill the fake progress bar)

Right now the progress bar is simulated client-side timing. Replace it with **real Server-Sent Events (SSE)** so the frontend shows genuine node-by-node progress as the LangGraph actually executes.

- Backend: convert `/api/complaints/extract` to stream via SSE, emitting an event after each node completes (`{"node": "extract_entities", "status": "complete", "data": {...}}`)
- Frontend: replace the simulated timer in `ExtractionProgressBar.jsx` with an `EventSource` listener, so field population is driven by real backend events, not a guessed timeout
- This is a genuine engineering upgrade an interviewer will notice immediately — "is this real or simulated?" becomes "it's real" instead of an awkward explanation

## PHASE 6 — CHAT INTERACTIVITY (finish the AI Copilot properly)

Right now the AI panel shows the summary as a static first message. Make the chat actually interactive:

- Wire `chat_node.py` (already scaffolded, unused) to a real `/api/complaints/{id}/chat` endpoint
- Chat has full context: the extracted fields, risk reasoning, CAPA recommendation — user can ask "why is this Critical?" or "what should I do next?" and get grounded answers referencing the actual complaint
- Frontend: real `ChatInput.jsx` + `ChatMessageList.jsx` wired to Redux `chatSlice`, persisted to `chat_messages` table
- This is the single most "wow" feature left on the table — a reviewer typing a real question and getting a grounded answer is more impressive than any static UI polish

## PHASE 7 — RELIABILITY & ROBUSTNESS PASS

- **Retry logic**: wrap every Groq call with exponential backoff (3 attempts) for transient API failures
- **Rate limiting**: add basic rate limiting on `/extract` endpoint (e.g. `slowapi`) — shows production awareness
- **Input validation**: file size limits (10MB per the original spec), file type allowlist, malformed-file handling with clean error messages (not stack traces surfaced to UI)
- **Loading/error states everywhere**: every card should have a distinct loading, success, and error visual state — no silent failures
- **Graph-level error recovery**: if one node fails (e.g. Groq API down), the graph should still return partial results with a clear "this section failed" flag rather than crashing the whole request

## PHASE 8 — TESTING SUITE (this is what separates "demo" from "engineered")

- **Backend**: pytest coverage for every node individually (mock the Groq client, test parsing/validation logic in isolation) + integration test for the full graph + API endpoint tests via `TestClient`
- **Frontend**: component tests with Vitest + React Testing Library for at least the form, upload dropzone, and card components
- **E2E**: one Playwright test that uploads a sample file and asserts the full flow completes and fields populate — this is genuinely rare for a take-home assignment and will stand out
- Add a coverage badge to the README

## PHASE 9 — DEPLOYMENT (make it clickable, not just describable)

- **Frontend** → Vercel (same pattern as your EchoLog project)
- **Backend** → Render or Railway
- **Database** → Neon or Supabase (free-tier Postgres)
- **Environment separation**: proper `.env.production` vs `.env.development`, secrets never in git
- **CORS locked down** to the actual deployed frontend origin, not `*`
- Add the live URL prominently at the top of the README — this is what turns "trust me it works" into "click here"

## PHASE 10 — DOCUMENTATION & PRESENTATION

- **README.md**: architecture diagram (embed the mermaid graph), setup instructions, live demo link, screenshots/GIF of the extraction flow, tech stack badges, "why these design decisions" section (e.g. why rule-based duplicate detection over embeddings — shows judgment, not just execution)
- **ARCHITECTURE.md**: deeper technical doc — the LangGraph state contract, model routing rationale, database schema with ER diagram
- **API documentation**: FastAPI's auto-generated `/docs` (Swagger) is already there — add proper docstrings and examples to every route so it's genuinely useful, not just default-generated
- **WHAT_I_LEARNED.md**: honest reflection — what was hard, what you'd do differently, what you'd build next (this is the file you already know the drill on from the Tradexa assignment)

## PHASE 11 — OPTIONAL STRETCH (if you truly have unlimited time)

- **Docker Compose**: one-command local spin-up (`docker-compose up`) for backend + frontend + Postgres — huge credibility signal for a reviewer who wants to try it themselves
- **Analytics dashboard**: a second page showing aggregate stats across all logged complaints (severity distribution, top complaint types, average completeness score) — turns this from "single complaint tool" into "product with a management view"
- **Multi-language support hint**: given your ZaminSaathi experience with Kannada/English, even a stub for non-English complaint parsing would tie your portfolio together thematically
- **CI/CD**: GitHub Actions running the test suite on every push — free, fast to set up, and signals real engineering discipline

---

## Suggested order given "infinite time" but real priorities

1. Phase 6 (Chat) — biggest wow-per-effort ratio
2. Phase 5 (Real streaming) — biggest "is this real" credibility upgrade
3. Phase 8 (Testing) — biggest differentiator vs other candidates' submissions
4. Phase 7 (Robustness) — makes it genuinely production-feeling
5. Phase 9 (Deployment) — makes it clickable
6. Phase 10 (Docs) — makes it presentable
7. Phase 11 (Stretch) — only if still going strong

