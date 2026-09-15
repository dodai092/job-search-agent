# Fit-scoring rubric

Applied by the scheduled agent itself (no separate LLM API call — the agent
running this pipeline already is an LLM) to every posting that survives
`hard_filter.py`. See SPEC.md "Matching".

## Inputs

- The posting's title, description, employer, and any geo field
  (`job_geo` / `candidate_required_location` / `locations`).
- Antun's CV: `/Users/antunzebec/Documents/AZebec/ANTUN ZEBEC CV, April 2026.docx`
- `criteria.yaml` (target roles, seniority, employment type)

## Score: 1-10

Rate how well Antun's actual background (AI/LLM automation — n8n, RAG,
OpenAI/PydanticAI; web dev — Webflow/Framer; plus recent AI eval work at
Mercor) matches what this specific posting is asking for. Not a generic
"is this a good job" score — a fit score against *his* CV.

- **8-10**: Directly matches his core skills (AI automation, RAG/LLM
  integration, n8n/workflow orchestration, or Webflow/Framer web dev) at a
  seniority level he can credibly claim.
- **5-7**: Adjacent fit — e.g. a general backend/software role where his AI
  work is a plus but not the core ask, or a role slightly above/below his
  demonstrated seniority.
- **1-4**: Weak fit — different domain entirely, or a hard mismatch (e.g.
  requires years of experience in a stack he doesn't have).

## Rationale

One sentence, quoting or closely paraphrasing the specific requirement that
drove the score — not a generic summary. If a required field (seniority,
employment type, geo-eligibility) isn't stated in the posting, say
"unknown" rather than assuming a value. This mirrors criteria.yaml's own
rule for the location filter — don't infer what isn't stated.

## Threshold

**Start at 6.** Only postings scoring ≥6 get written to the Sheet.

This is a starting guess, not a calibrated value — there's no data yet on
what a good cutoff looks like (see SPEC.md Open questions). After the first
few real runs, review the Sheet's actual score distribution and adjust this
number based on what a human read of the postings suggests the cutoff
should have been.
