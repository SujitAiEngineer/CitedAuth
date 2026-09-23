# Decision Guardrails

Read this before applying the policy criteria to a request. These are process
rules, not clinical criteria — the clinical criteria live in `policy_criteria.md`.
If the two ever conflict, `policy_criteria.md` wins on clinical substance; this
file governs how you use it and how you report your answer.

## Output contract

Every determination is exactly one of: `approve`, `deny`, `needs-info`.

`urgent` is a **separate boolean flag**, not a fourth determination. A request
can be `approve` AND `urgent` at the same time (see Example 4 below) — urgent
means "a human needs to see this regardless of what the automated outcome was,"
per the policy's cross-cutting rule 2. Never fold urgency into the determination
value itself.

Always include:
- `policy_id` — the exact policy ID that drove the outcome (e.g. `LMB-114`).
- `criterion` — the specific numbered criterion(s) that drove the outcome, not
  just "criteria 1-3." If you denied on criterion 2 specifically, cite criterion 2.
- `reason` — one or two sentences, plain and specific, tying the clinical note's
  actual facts to the criterion cited. Not a restatement of the policy text.

## The rule most likely to be gotten wrong: absence vs. negation

If the clinical note is **silent** on a required data point, the answer is
`needs-info`, never `deny`. Denying requires an affirmative fact that fails a
criterion (e.g., "PT tried for only 2 weeks"). Missing documentation is not
a negative finding — it's missing documentation.

- "BMI documented in chart" with no number given → the value is absent, not
  known-to-be-too-low. That's needs-info, not deny.
- A psychological evaluation that is simply never mentioned in the note → absent,
  not "not completed." Needs-info.
- Contrast with an affirmative failure: "conservative therapy not attempted" is
  a stated negative fact, and can support a deny.

When a request has *both* an affirmative failure on one criterion and a missing
data point on another, needs-info still wins — you can't issue a clean deny when
part of the picture is incomplete. Flag what's missing specifically.

## Red flags bypass, but never bypass the urgent flag

Each policy lists its own red-flag / bypass conditions (e.g. LMB-114's
neurological deficit, new bowel/bladder dysfunction, suspected cauda equina,
malignancy history, suspected infection). If any is present, approve
immediately without checking the standard numbered criteria — but still set
`urgent = true` and say so in the reason, per cross-cutting rule 2 ("any request
where the clinical note suggests an urgent or emergent condition must be
flagged for immediate clinical review regardless of the procedure-level
outcome"). The bypass changes the determination path, not whether a human
needs to see it fast.

## Match only the policy for the requested procedure

Don't apply criteria from a different policy section. If the `procedure` field
doesn't map to any policy you were given, do not guess or approximate — return
`needs-info` with a reason stating the procedure isn't covered by an on-file
policy.

## When genuinely uncertain

If the note's facts don't clearly resolve to approve or deny under the cited
policy, prefer `needs-info` over guessing. A wrong needs-info costs a manual
review; a wrong approve or deny costs a mis-adjudicated claim.

## Worked examples (patterns, not just answers)

1. **Duration + conservative therapy both met, no prior imaging** → all
   numbered criteria satisfied → `approve`, citing each criterion met.
2. **Symptom duration far under the threshold, no conservative therapy
   documented, no red flags** → two affirmative failures → `deny`, citing the
   specific criteria numbers that failed.
3. **Imaging on file showing the structural finding, conservative care
   documented past the threshold, mechanical symptoms present** → `approve`.
4. **A required duration is under threshold (e.g., program participation
   shorter than required) AND a required value is mentioned but not actually
   given AND another required element is never mentioned at all** →
   `needs-info` — multiple missing/incomplete data points, not a clean fail.
   List each gap.
5. **Symptomatic presentation with an equivocal prior test, matching an
   "any of the following" approval clause** → `approve` on the clause that's
   satisfied, even if other clauses in the same list aren't addressed.
6. **A red-flag condition (progressive neuro deficit, new bowel/bladder
   involvement, etc.) present alongside an otherwise-incomplete standard
   workup** → `approve` via the red-flag bypass, `urgent = true`, reason
   states which red flag fired.
7. **No imaging on file and no conservative therapy documented, policy's
   explicit deny clause matches** → `deny`, citing the deny clause directly.
8. **Asymptomatic surveillance/screening request that the policy's deny
   clause explicitly excludes** → `deny`, citing that clause by name.
