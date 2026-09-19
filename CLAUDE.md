# Project rules

This is a live, time boxed build. I am being watched and graded on reasoning,
not on volume of code. Follow these rules on every turn.

## Working agreement

- Small diffs. One concern per change. Never refactor unasked.
- The app must be runnable after every single change. If a change would break
  startup, stub the missing piece instead.
- Prefer stdlib and already installed packages. Do not add a dependency without
  telling me first and saying why.
- Never run `pip install` or `npm install` without asking.
- After any change that affects how the app runs, print the exact command to run it.
- If something fails twice the same way, stop and say so plainly. Do not spiral.

## Stack

- Backend: FastAPI, `backend/app/main.py`, run with
  `.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000`
- Frontend: React via Vite in `frontend/`, dev server on 5173. Optional.
  Do not build UI until the API works via curl.
- Agents: LangGraph preferred. Keep graph definition in `backend/app/agents/graph.py`.
- Tools: one file per tool in `backend/app/tools/`, each a plain function with a
  docstring and typed args.
- Data: anything the interviewer hands me goes in `backend/data/`.

## Code style

- Type hints on function signatures.
- Pydantic models for every request and response body.
- No bare excepts. Catch what you expect and let the rest surface.
- Docstrings say why, not what.

## Build discipline

- Vertical slice first: one input, one path through the system, one visible output.
- Breadth later. A working narrow path beats four half wired agents.
- Fake the expensive parts early with hardcoded returns, label them `# STUB`,
  and keep a running list of what is faked.
- Log every model call's token usage. I want to talk about cost on camera.

## What I care about out loud

When you make a non obvious choice, add one line saying what you traded away.
I will read those lines to the interviewer.
