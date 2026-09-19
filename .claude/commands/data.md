---
description: Inspect and qualify the input data before designing anything
---

Inspect the data I have been given. Path or description:

$ARGUMENTS

If no path is given, look in `backend/data/` and use what is there.

Write a short script in `scratch/inspect.py`, run it, and report. Do not paste
the whole dataset into the conversation. I want the shape, not the contents.

Report these, in this order:

## What it is
Format, size, row and column count, or for an API the endpoints and auth shape.

## Fields
A table: name, type, example value, null percentage, distinct count.
Flag anything where distinct count equals row count (likely an ID) or equals
one (likely useless).

## Quality problems
Nulls that matter, inconsistent formats, duplicates, encoding issues,
free text where you expected structure, dates that are strings.
Rank them by how much they threaten the build.

## What this rules in and out
The important part. Given this data, which approaches are now off the table,
and which became obvious? Be specific. "No labels, so supervised classification
is out, this has to be LLM judgement with a rubric" is the kind of line I want.

## Smallest usable slice
Which subset of rows and columns is enough to prove the path end to end?
Name it precisely so I can build against it immediately.

## What I would ask for
Any field or source that is missing and would change the design if I had it.

Keep it factual. No architecture yet.
