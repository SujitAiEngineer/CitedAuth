---
description: Turn a raw problem dump into a one page framing brief
---

I have just been handed a problem in a live interview. Below is my unstructured
dump of what they said, what I noticed, and my initial instincts.

$ARGUMENTS

Produce a framing brief. Write it to `scratch/01_frame.md` and print it.
Keep the whole thing under one screen. Use this exact structure:

## Problem
One sentence. The business problem, not the technical one.

## End user
Who touches this and what they do right after they get the output.

## Decision supported
What decision does this output change? If it changes no decision, say so
plainly, that is a finding worth stating out loud.

## Success metric
One primary metric, measurable. Plus the guardrail metric that stops me from
gaming the primary one.

## Assumptions
Three to five. Mark each one as SAFE or RISKY. For each RISKY one, note the
single question I should ask the interviewer to kill the risk.

## Scope
- In for today: the vertical slice I can demo in the time left
- Out, needs a week: what I would build next and why it is not now

## Open questions
Two or three, phrased as I would actually ask them.

Do not propose an architecture. Do not write code. Framing only.
If my dump is missing something you need, list what is missing rather than
inventing it.
