---
description: Generate an eval runner and an empty case file for me to hand label
---

Build a small eval harness for what I have already built.

Anything I want to specify (entry point, what counts as correct, how many cases):

$ARGUMENTS

## Before you write anything

Read the current code and work out, from the code itself and not from my
description:

- The entry point to evaluate. Prefer a plain Python function over an HTTP
  route. If only a route exists, call it with httpx against localhost:8000.
- The exact input shape it takes.
- The exact output shape it returns.
- Which single field is the thing being judged (the label, the decision, the
  routed queue). If the output has several fields, judge one primary field and
  report the rest for eyeballing.

Print those four findings in one short block before writing code. If you cannot
determine them from the code, say so and stop. Do not guess.

## Hard rule

You do NOT write expected outputs. Not one. You do not invent test inputs that
come with answers attached. The whole point of this harness is that a human
labeled the cases, so a model writing the answer key destroys its value and I
will have to say so out loud.

You may write input text for cases. You may never write the expected field.
Every expected value is the literal string `FILL_IN`.

## Write `evals/cases.jsonl`

One JSON object per line. Exactly 5 lines. Each object:

    {"id": "c1", "input": {...}, "expected": "FILL_IN", "note": "why this case exists"}

Make the five cases cover, and say in `note` which is which:
1. an obvious, unambiguous case
2. a second obvious case from a different class
3. a genuinely ambiguous case where two answers are defensible
4. an edge case: empty, truncated, or malformed input
5. a case that should fall below confidence and go to a human

Fill `input` with realistic content. Leave every `expected` as `FILL_IN`.

## Write `evals/run_evals.py`

Plain Python, stdlib plus what is already installed. No pytest, no new deps.

It must:

- Load `cases.jsonl`. If any `expected` is still `FILL_IN`, print
  `N of 5 cases are unlabeled. Fill them in before trusting this score.`
  and still run, marking those cases SKIPPED rather than passing them.
- Run each case through the entry point.
- Compare only the primary field, case insensitive, stripped.
- Print one line per case: `PASS`, `FAIL`, or `SKIP`, the id, and the note.
- For each FAIL print expected vs actual on the next line, indented.
- Print a summary: `X passed, Y failed, Z skipped out of 5`.
- Print total tokens and wall clock seconds across the run.
- Catch exceptions per case so one bad case cannot kill the run. A case that
  raises is a FAIL with the exception text as actual.
- Exit 0 always. This is a reporting tool, not CI.

Keep it under 80 lines. I need to be able to read it aloud.

## Finally

Print the exact command to run it, and one line telling me to go fill in the
five expected values by hand.
