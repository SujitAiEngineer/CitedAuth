---
description: Produce three architecture options with tradeoffs, then a recommendation
---

Using `scratch/01_frame.md` and `scratch/02_data.md` if they exist, plus anything
I add here:

$ARGUMENTS

Write to `scratch/03_architecture.md` and print it.

## Three options

Give exactly three, genuinely different in kind, not three flavours of the same
thing. Typically something like: single agent with tools, supervisor graph with
specialists, deterministic pipeline with one model call at the judgement step.
Pick the three that actually fit this problem.

For each option, four lines only:
- Shape: what the components are and how control flows
- Wins: what it is good at here
- Costs: latency, token spend, failure modes, how hard it is to debug live
- When it is the right call: the condition under which I would choose it

## Recommendation

One option. Say why, in terms of the success metric from the framing brief, not
in terms of elegance. Name the single thing that would make me switch to a
different option.

## Diagram

A mermaid flowchart of the recommended option. Components, data flow, and where
the model is called. Keep it under twelve nodes.

## Contracts

A table of every agent or node: name, one line responsibility, input type,
output type, the tools it can call.
Then a table of every tool: name, signature, what it returns, whether it has
side effects.

## Failure plan

For each model call: what happens on timeout, on malformed output, on refusal.
One line each. This is the part most candidates skip.

## Build order

Numbered steps for the vertical slice, smallest first. Each step must leave the
app runnable. Mark which steps I will stub.

Do not write implementation code yet.
