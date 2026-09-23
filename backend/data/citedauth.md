# CitedAuth

CitedAuth is a prior authorization review tool built for a regional health
plan whose nurse reviewers were taking about five days to adjudicate each
request, against a two-day regulatory turnaround clock. It automates the
first pass of that review: reading a clinical note, matching it against the
plan's coverage policy, and producing a determination (approve / deny /
needs-info) with a citation back to the specific policy and criterion that
drove the outcome — the same shape of answer a nurse reviewer would produce,
but in seconds instead of days.

The name is a statement of intent: every determination is *cited*, not just
asserted. If the model can't point to a specific policy ID and criterion
number, that's treated as a failure mode, not an acceptable answer.

## What it actually does, end to end

1. A nurse uploads an Excel sheet of prior authorization requests (columns:
   `request_id`, `member_id`, `age`, `procedure`, `clinical_note`,
   `requesting_provider`).
2. She clicks **Analyze**. For every row, the backend runs one LLM call
   against the matching coverage policy and a guardrail file, and gets back
   a structured determination: `approve`, `deny`, or `needs-info`, plus the
   policy ID, the specific criterion cited, a reason, and an `urgent` flag.
3. Results render in a table in the browser. Above the table: aggregate
   input/output token counts and total latency for the batch, so cost is
   visible on the spot. Each row also has its own **LLM Input** / **LLM
   Output** columns (truncated, click "show more" for the full text in a
   popup) — the exact prompt sent and the exact response received for that
   row's decision.
4. The nurse checks the rows she wants letters for (checkbox per row, plus
   select-all / deselect-all). Checking a row and generating its letter *is*
   her sign-off — there is currently no separate edit/override step before
   a determination becomes a letter. That's a deliberate scope cut for this
   build, not an oversight (see "Known gaps" below).
5. **Generate letters (PDF)**: for each selected row, a second LLM call
   turns the terse structured `reason` into a short provider-facing prose
   paragraph. All selected letters are assembled into one multi-page PDF
   (header, date, To: the requesting provider, the determination, the
   policy citation, the prose reason, signed "Nurse on Duty") and the
   browser downloads it automatically.
6. The full results table can also be downloaded as an xlsx for the nurse's
   own records.

Every model call — both the per-row decision and the letter-prose call — is
logged to the backend terminal in full: the complete input sent, the
complete output received, input/output token counts, and latency in
milliseconds. Nothing about what the model saw or said is hidden.

## Tech stack

**Backend** — Python, FastAPI (`backend/app/main.py`), run with Uvicorn.
- **LangGraph** (`backend/app/agents/graph.py`) orchestrates the per-row
  decision as a two-node graph: `match_policy` (deterministic dictionary
  lookup into `policy_criteria.md`) → `decide` (the one LLM call). A
  conditional edge skips the LLM entirely if a request's procedure doesn't
  match any on-file policy, so an unmapped procedure returns `needs-info`
  instead of the model guessing.
- **Anthropic Claude** via the `anthropic` Python SDK. The `decide` call
  uses forced tool-calling (`tool_choice: {"type": "tool", ...}`) against a
  `submit_determination` tool schema, so the response is always structured
  JSON rather than free text that needs to be parsed. The letter-prose call
  (`summarize_reason`) is a plain text completion.
- **Pydantic** (`backend/app/models.py`) defines every request/response
  shape: `PriorAuthRequest`, `DeterminationResult`, `AnalyzeResponse`,
  `TokenUsage`.
- **openpyxl** for reading the uploaded xlsx and writing the results xlsx
  back out (`backend/app/tools/xlsx_io.py`).
- **fpdf2** for PDF letter generation (`backend/app/tools/pdf_letter.py`) —
  pure Python, no system dependencies, chosen over `reportlab` for being
  lighter weight than a one-page-letter task needs.
- **python-dotenv** loads `ANTHROPIC_API_KEY` and `MODEL` from `.env`
  (never committed — see `.gitignore`).

**Frontend** — React 19 + Vite (`frontend/`), dev server on port 5173.
Plain `fetch` calls to the backend, no state management library, no UI
framework — component state via `useState`, inline styles. Deliberately
minimal: the interview brief was explicit that the API should work via curl
before any UI got built at all.

## Repository layout

```
backend/
  app/
    main.py                 FastAPI app, all HTTP routes
    models.py                Shared Pydantic models
    agents/
      graph.py               LangGraph: match_policy, decide, summarize_reason
    tools/
      xlsx_io.py              Parse uploads, write results xlsx
      policy_lookup.py        Parses policy_criteria.md into per-procedure sections
      pdf_letter.py            Deterministic PDF assembly (no model calls)
  data/
    policy_criteria.md        The plan's coverage policy (source of clinical truth)
    knowledge.md               Guardrail rules the decide call reads before answering
    prior_auth_requests.xlsx  8-row sample dataset used to build and test this
    citedauth.md                This file
frontend/
  src/
    App.jsx                   Upload, Analyze, results table, letter generation
    main.jsx
  vite.config.js
```

## The guardrail file (`knowledge.md`)

`policy_criteria.md` holds the plan's actual clinical criteria (per
procedure: what to approve, what to deny, what red flags bypass the normal
criteria). `knowledge.md` is a separate, smaller file the `decide` call also
reads — it governs *how* the model is supposed to use that policy, not the
clinical substance itself. Its most important rule, and the one most likely
to be gotten wrong: if the clinical note is silent on a required data point,
the correct answer is `needs-info`, never `deny` — absence of documentation
is not the same as a negative finding. It also separates the `urgent` flag
from the determination itself (a request can be `approve` *and* `urgent` at
the same time, per the policy's cross-cutting rule that any note suggesting
an emergent condition gets flagged for human review regardless of outcome),
and it mandates that every determination cite a specific policy ID and
criterion number.

## Design choices worth knowing about

- **One LLM call per row for the decision**, not an agent with tools and
  not a multi-step supervisor graph. The procedure-to-policy mapping is
  small and fixed (four procedures, four policies) for this build, so
  dynamic policy search would be solving a problem the data doesn't have;
  and a single well-grounded call minimizes the places variance can enter,
  which matters directly for the accuracy metric this tool is judged on.
- **Every failure mode fails safe to `needs-info`**, never to `approve` or
  `deny`. A timeout, a malformed response, or a model refusal on the decide
  call all produce a `needs-info` result with a reason explaining that
  manual review is required. The letter-prose call fails differently: on
  failure it falls back to the original structured reason verbatim, because
  by the time that call runs the actual decision has already been made
  safely — a prose failure there degrades letter quality, it never blocks
  the download.
- **No backend persistence.** Results from `/api/analyze` live only in the
  frontend's React state; generating letters sends the selected rows back
  to the backend rather than the backend looking anything up by ID.

## Known gaps (explicitly out of scope for this build)

- No edit/override step between a determination and its letter — checking a
  row for letter generation is currently the nurse's only checkpoint.
- The deterministic `guardrail_check` post-check (an extra safety net for
  the absence-vs-negation rule, separate from asking the model to follow it
  in the prompt) is designed but not wired into the graph yet.
- Policy matching is hardcoded to the four procedures in
  `policy_criteria.md`; there's no handling for a larger policy library.
- No legally-reviewed appeal-rights language in the letter template.
- No authentication, no multi-user support, no audit log beyond the
  terminal's per-call logging.

## Running it

```
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```
```
cd frontend
npm run dev
```
