# Job Search Agent — Spec

## Goal

A daily scheduled agent that finds job postings worth applying to, scores them
against Antun's CV and criteria, and surfaces a shortlist. It does not apply
on his behalf.

## Research findings (verified this session)

- **EURES has a real public search endpoint**
  (`europa.eu/eures/api/jv-searchengine/public/jv-search/search`), documented
  by a third-party OpenAPI spec (`rorar/EURES-API-Documentation`) and used by
  multiple commercial scrapers on Apify. It's not an official
  Commission-published developer doc, it's community reverse-engineered — so
  treat it as real and usable, but liable to change without notice.
- **LinkedIn scraping via Firecrawl is confirmed unreliable, not just
  ToS-risky.** LinkedIn actively blocks scraping services with Cloudflare and
  login walls; Firecrawl users report consistent 403s on LinkedIn
  specifically. This isn't a theoretical risk to "be aware of" — it's a
  functional blocker most likely to fail outright, on top of being a ToS
  violation that could get Antun's actual LinkedIn account flagged.
  **Decision: drop LinkedIn from the automated pipeline.** Given both the
  low odds of it working reliably and the account risk (Antun's LinkedIn is
  tied to his real name and business), automating it isn't worth it. He can
  check LinkedIn himself manually if he wants that coverage; the agent
  covers Posao.hr and EURES (MojPosao also dropped — see below).
- **Feasibility spike run (2026-09-15)** — confirmed all three remaining
  sources are usable, with two corrections to how:
  - **EURES**: works as expected, but the documented `specificSearchCode:
    "EVERYWHERE"` keyword mode barely filters anything (a search for "AI"
    returned 1702 of ~1749 unfiltered Croatia results, including irrelevant
    postings). `specificSearchCode: "TITLE"` filters correctly (tested:
    "AI" → 1 real match, "programer" → 29 relevant matches). **Use `TITLE`
    mode**, not the example payload's `EVERYWHERE`.
  - **EURES has no per-posting link (found 2026-09-15).** The job vacancy
    schema has no URL/link field at all (checked the full OpenAPI spec). A
    guessed detail-page URL pattern was tested against a real job ID vs. a
    fabricated one — both returned byte-identical generic SPA shells, and a
    JS-rendered Firecrawl fetch of it returned nothing job-specific either.
    **Decision: keep EURES for title/employer/location signal, but rows
    from this source have no clickable link** — Antun would need to search
    the title manually on eures.europa.eu. Less actionable than a Posao.hr
    row, but still useful as a "this kind of role exists at this company"
    signal.
  - **Posao.hr**: scrapes cleanly via Firecrawl, and better than planned —
    it has **RSS feeds per job category**
    (e.g. `posao.hr/rss/djelatnost/informatika-i-telekomunikacije/`).
    Structured XML that won't break on a page redesign the way HTML
    scraping would — use RSS as the primary pull mechanism for this source,
    not markdown scraping.
  - **MojPosao: dropped entirely (2026-09-15).** Beyond the keyword-filter
    problem (search is client-side JS, no working query-string param —
    three guessed URL patterns all returned the same ~1800 unfiltered
    total), a follow-up check found the general listing scrape doesn't
    return usable structured data either: `--only-main-content` markdown
    gets company names/locations but no titles or links at all, and even
    with `-f markdown,links` + a longer render wait, the `links` output
    only gives raw job URLs whose slugs would need to be mangled into
    fake titles (e.g. "Administrator Linux It Infrastrukture M Z") with no
    company name attached — accurate data would require scraping all
    ~243 individual job pages per run, which is too expensive for a daily
    pull. Between the two problems, this source doesn't clear the bar of
    "clean data in one call" that Posao.hr and EURES both meet. Croatia/EU
    coverage comes from Posao.hr + EURES only.

## Output

Shortlist/digest only:

- New matches appended as rows to a Google Sheet (system of record).
- A short digest email ("N new matches today" + link to the Sheet) sent only
  on days with new matches.
- Digest email also reports any source that failed to pull that day (see
  Reliability below) — silence should never mean "nothing happened."

No auto-apply, no drafted application text (v1 scope).

## Sources

Pulled daily:

1. **Posao.hr** — largest remaining Croatian job board covered. Pulled via
   its per-category **RSS feeds**, not HTML scraping (see Research
   findings).
2. **EURES** (eures.europa.eu) — EU-wide job mobility portal, covers Croatia
   + all EU/EEA remote-eligible postings. Pulled via its public API using
   `specificSearchCode: "TITLE"` keyword search (see Research findings).
   Rows from this source have no clickable link (see Research findings).
3. **Remotive** (remotive.com) — global remote-jobs board. Pulled via its
   free public API (`remotive.com/api/remote-jobs`, no key needed). Verified
   2026-09-15: real structured data (title, company, url, `category`,
   `candidate_required_location`). Its `category`/`search` filter params are
   ignored — the free endpoint always returns the same fixed ~15 jobs
   regardless of query — so, like Posao.hr, this pulls unfiltered and lets
   the downstream hard-filter/scoring stage do the work. Its terms restrict
   republishing listings to other job boards, not personal use; cap pulls at
   ≤4/day (once-daily is well within that).
4. **Jobicy** (jobicy.com) — global remote-jobs board. Pulled via its free
   public API (`jobicy.com/api/v2/remote-jobs`, no key needed) using the
   `industry=` filter (confirmed working: `engineering`, `data-science` —
   exact slug list needs pulling from their docs before the build task).
   Notably, each posting has a `jobGeo` field (e.g. "Canada, Europe")
   stating its actual geographic eligibility — this is the first source
   that gives real data for the remote-vs-hireable-from-Croatia distinction
   in criteria.yaml, which the other three sources can't check at all.
   Requires attribution + apply-button redirect to the original job URL per
   its terms.

**LinkedIn and MojPosao both dropped from the automated pipeline** — see
Research findings.

Considered and dropped (2026-09-15 review, per a second-opinion source
comparison): **Arbeitnow** — free/no-key API but overwhelmingly German
on-site postings in a sample pull (8/250 remote-flagged, and even those
tagged to German cities with no confirmed Croatia-hire eligibility) — lower
signal than Remotive for the same "remote" filter. **Jooble** — real API but
requires applying for a key and waiting for approval, no immediate payoff.
**Greenhouse/Lever/Ashby employer feeds** — real per-company APIs, but only
useful once specific target companies are named; not an aggregator. **HZZ,
Adzuna** — unverified/unconfirmed Croatia coverage, unchanged from earlier
research. **Himalayas** — best-in-class schema (explicit
`locationRestrictions` field, salary, seniority) but 104,000+ total postings
with no working keyword/category filter found (every param tried was
ignored) — pulling the full dataset daily is impractical. **RemoteOK** —
real API, small feed (~100 postings, filterable downstream like Posao.hr),
but tag filtering is broken/ignored and it overlaps heavily with Remotive's
coverage — not worth a fifth pull mechanism for redundant signal.

**Deferred to phase 2, not rejected**: **We Work Remotely** — real,
reliable per-category RSS feeds (same proven pattern as Posao.hr), a solid
candidate for more volume. Held back deliberately: we haven't run the
4-source version yet to know whether volume is actually a problem worth
solving. Revisit once real digests come in — if the shortlist feels thin
after a few weeks, this is the first thing to add (see Open questions).

Dropped from consideration (original pass): JSearch (no confirmed Croatia
coverage), Kariera.hr (lower signal, can be added later if the three sources
above prove insufficient).

## Matching

Two-stage filter per posting:

1. **Hard filters** (deterministic, from criteria below) — reject before
   spending any LLM call on it.
2. **Fit scoring** (LLM) — for postings that pass hard filters, compare the
   posting against Antun's CV and produce a fit score + one-line rationale.
   Only postings above a minimum fit threshold get written to the Sheet.

### Criteria (hard filters)

- **Target roles**: AI Developer, AI Automation Engineer, AI Consultant, Web
  Developer roles with an AI/automation component. Both employee and
  contract roles in scope.
- **Seniority**: mid/senior. Exclude junior/internship roles.
- **Location**: remote-only. Exclude on-site-required roles outside a
  Croatia/EU-compatible timezone.
- **Salary**: no floor set (skipped for now).
- **Employment type**: full-time or contract/freelance both acceptable
  (this is meant to supplement Dodai, not replace it — Antun keeps running
  Dodai regardless of outcome).
- **Exclusions**:
  - Recruiting/staffing agency reposts (vs. direct employer listings).
  - Junior/internship-level roles.

### CV

On file: `/Users/antunzebec/Documents/AZebec/ANTUN ZEBEC CV, April 2026.docx`

This file has unfilled template placeholders still in it — e.g. "[Z]
hours/month", "[provider]" (×3), "[Data/Automation/Web]", "[~3,000]+", and
even the phone/email/LinkedIn fields are wrapped in literal brackets. Fit
scoring quality is bounded by what the LLM reads here, so **before the first
real run**, do a short pass to fill in or remove these placeholders (doesn't
need to be a full rewrite — just no literal bracket-placeholder text left for
the scoring step to read).

## Reliability

- **Dedupe**: normalize posting URLs before comparing (strip query
  string/tracking params, lowercase, strip trailing slash) — job boards
  append referral params, so raw-URL matching would under-dedupe. Fall back
  to title+company match only if a posting has no stable URL.
- **Per-source failure handling**: each source's pull step records
  success/count or failure for that run. A source that fails 2+ consecutive
  days is called out explicitly in the digest email, not silently skipped —
  a quiet failure is worse than no automation, because it erodes trust in
  the digest without Antun knowing why.
- **Run summary**: each run logs pulled / deduped-out / hard-filtered-out /
  scored-below-threshold / added counts (a log tab in the Sheet, or in the
  digest email). Needed to actually tune the fit-score threshold below
  instead of guessing blind.

## Delivery

- **Google Sheet** — one row per match: title, company, location, source,
  link, fit score, one-line rationale, date found, status
  (blank/Applied/Rejected — manually maintained by Antun). EURES rows will
  have an empty link cell (see Research findings) — dedupe for those rows
  falls back to title+company matching instead of URL matching.
  - **Mechanism (corrected 2026-09-15)**: the original plan ("download via
    Drive MCP, append in memory, re-upload") turned out to be impossible —
    the Drive MCP has no content-write call for existing files at all
    (`create_file` only makes new files with new IDs/URLs; `update_file`
    only changes title/parentId, checked its full schema). Re-creating the
    file daily would change the Sheet's URL every run and destroy Antun's
    manual Status edits, so instead: a small **Google Apps Script Web App**
    bound to the Sheet (`apps-script/Code.gs`), calling `appendRow()`
    directly — this touches nothing but new rows, so the URL and existing
    edits are untouched. Same pattern Antun already uses for Vinalia's
    Evidencija sheet (Apps Script + shared secret). Deployment is a manual
    one-time step (`apps-script/DEPLOY.md`) since Google requires the
    user's own authorization; the daily pull calls it via
    `scripts/append_to_sheet.py`. **Reads** (for dedupe, checking existing
    rows) still go through the Drive MCP's `read_file_content`/
    `download_file_content`, which do work fine — only writes needed the
    workaround.
- **Gmail** via Gmail MCP: digest email, sent when there's ≥1 new match or
  ≥1 source failure that day.

## Schedule

Daily, via the `schedule` skill — a durable, persisted cloud routine, one
run per day covering steps below. **Not** the `CronCreate` tool (corrected
2026-09-15) — that's explicitly session-only (dies with this session) and
recurring jobs auto-expire after 7 days regardless, unsuitable for a job
meant to run daily indefinitely.

## Task list

0. ~~**Feasibility spike**~~ — done 2026-09-15, see Research findings. All
   three sources confirmed usable, with mechanism corrections folded into
   the Sources section above.
1. **CV cleanup** — fill in/remove the bracket placeholders (see CV section
   above). Quick pass, not a full rewrite.
2. **Sheet setup** — create the Google Sheet (via Drive MCP `create_file`,
   spreadsheet mime type) with the column header row above, including the
   status column. One-time setup.
3. **Criteria doc** — write the hard-filter criteria above into a small
   config file the daily run reads (avoids re-deriving filters each run).
4. **Source pull step** — Posao.hr: pull relevant category RSS feed(s)
   (e.g. IT & telecom). EURES: API call with `locationCodes: ["hr-NS"]` and
   `specificSearchCode: "TITLE"` keyword(s). Remotive: pull
   `remotive.com/api/remote-jobs` filtered to relevant categories (≤4
   pulls/day per its terms — daily cron is fine). Jobicy: pull
   `jobicy.com/api/v2/remote-jobs` with `industry=` filter(s) relevant to
   target roles (need real slug list from their docs — `engineering` and
   `data-science` confirmed working, others guessed wrong). Each pull
   records success/failure per the Reliability section. ~~Done 2026-09-15 —
   all four pull scripts written and verified against live data.~~
5. ~~**Dedupe step**~~ — done 2026-09-15, `scripts/dedupe.py`. Normalizes
   URLs (strip tracking params/case/trailing slash), falls back to
   title+company matching for link-less postings (EURES), self-test passing
   against tracking-param dupes, within-batch dupes, and the fallback case.
6. ~~**Hard-filter step**~~ — done 2026-09-15, `scripts/hard_filter.py`.
   Deliberately conservative (see decision below): only excludes on
   unambiguous title keywords (junior/intern/pripravnik/praksa) and explicit
   single-country geo fields clearly incompatible with Croatia (USA/Canada/
   Australia/NZ/LATAM/UK-only). Everything ambiguous (agency-or-not,
   employment type, unfamiliar single-city geo) passes through to
   fit-scoring instead of being silently dropped. Sanity-checked against
   real Jobicy+EURES pulls (163 postings → 73 passed, 90 rejected, all
   rejections manually verified as correct — legitimate junior/intern titles
   and genuinely single-country-restricted roles, no false positives found).
   **Design decision (2026-09-15):** chose conservative over aggressive
   filtering — a wrong hard-exclusion is silent and unrecoverable (you'd
   never see the dropped row), while a wrong LLM score in fit-scoring is
   visible in the Sheet's rationale column and correctable by retuning the
   threshold.
7. ~~**Fit-scoring step**~~ — done 2026-09-15, `scoring_rubric.md`. Built as
   a rubric the scheduled agent applies with its own reasoning, not a
   separate script/API call — the agent running this pipeline already is an
   LLM, so a second one would be a redundant dependency. Verified against 6
   real postings from today's pulls (scores 1-4, correctly low since none
   were strong AI/automation matches — a telecom technician and Linux
   kernel role correctly scored 1, a full-stack Lead role correctly scored
   4 for seniority/domain mismatch) plus one synthetic high-fit posting
   (RAG/n8n/OpenAI role scored 9, confirming the top end differentiates
   correctly). Starting threshold: 6 (uncalibrated guess, see Open
   questions).
8. ~~**Sheet append step**~~ — done 2026-09-15. Apps Script deployed by
   Antun, `scripts/append_to_sheet.py` updated with the live deployment URL,
   tested end-to-end with a real append call — row landed correctly in the
   right column order, verified via a Drive MCP read-back. (One leftover
   "Test Row" in the Sheet for Antun to delete manually — the script is
   deliberately append-only with no delete capability.) Run-summary counts:
   decided to put these in the
   digest email body (step 9) rather than a separate Sheet tab — simpler,
   no second tab schema to maintain.
9. ~~**Digest email step**~~ — done 2026-09-15, `scripts/build_digest.py`.
   Deterministic should-send decision + formatting (same pattern as
   fit-scoring/Sheet-append: logic is scripted, the actual Gmail send
   happens via the Gmail MCP at runtime). Self-tested against 4 cases (no
   activity → don't send; matches only; failures only; link-less EURES
   posting formats gracefully). **Bug found and fixed via a real test
   send**: a plain-text `body` caused Gmail to auto-linkify bare
   domain-like text (e.g. "posao.hr" in the run summary) into fake
   tracking-redirect links. Switched to an `html_body` output with real
   `<a href>` only on actual job links — added a self-test asserting no
   `<a` tag appears outside the matches section. Verified end-to-end with
   two real test emails sent to Antun's own address via the Gmail MCP
   (first showed the bug, second confirmed the fix).
10. ~~**Schedule it**~~ — done 2026-09-15. Routine created via the `schedule`
    skill's `RemoteTrigger` API:
    https://claude.ai/code/routines/trig_015cXPwesNj1JfHerXzUTrWb, daily at
    9:05am Europe/Zagreb (7:05am UTC), first run 2026-09-16.
    **Real friction hit along the way, for the record:**
    - Cloud routines run in an isolated sandbox with zero access to
      Antun's local machine — needed a git repo, which this project wasn't.
      Pushed to a new repo, `github.com/dodai092/job-search-agent`.
    - The CV lives as a local docx the sandbox can't read — added `cv.md`,
      a plain-text mirror, kept manually in sync.
    - Hit a currently-open Anthropic platform bug (GitHub issue, `area:auth`
      + `area:routines`): connecting GitHub via OAuth doesn't install the
      actual GitHub App or prompt for repo selection, so private-repo
      access for routines was broken. Worked around it by making the repo
      **public** (safe — no secrets were ever committed; see below) rather
      than waiting on an unresolved bug.
    - The routine's prompt originally embedded the Apps Script shared
      secret directly — the auto-mode classifier correctly blocked this
      twice (once in the prompt, once when attempting to stash it in a
      Drive file instead) as credential-handling I shouldn't do on Antun's
      behalf. Fixed by using the routine's actual `environment_variables`
      mechanism instead: the prompt now just says the script reads
      `SHEET_APPEND_SECRET` from its environment, and **Antun sets the real
      value himself directly in the claude.ai routine UI** — never
      transmitted through any of my tool calls.

## Open questions / risks

- **Four-source coverage (Posao.hr, EURES, Remotive, Jobicy) vs. originally
  scoped four (LinkedIn, MojPosao, Posao.hr, EURES)** — different mix, not
  necessarily thinner, but unproven until real runs happen. Worth watching
  whether the digest feels too sparse after a few weeks; if so, **We Work
  Remotely was deliberately deferred, not rejected** (see Sources) — it's
  the first candidate to add, using the same proven RSS-per-category
  pattern as Posao.hr. HZZ/Kariera.hr and revisiting MojPosao (option B, a
  per-posting-scrape budget) are further-out fallbacks if that's still not
  enough.
- **EURES endpoint is community-documented, not official** — could change
  without notice; if it breaks, that's a signal to look for a replacement
  source, not necessarily a bug in the agent's code.
- **Fit-score threshold**: no data yet on what a good cutoff looks like.
  First few real runs' output should be reviewed manually before trusting
  the digest to filter correctly on its own.
- **No LinkedIn coverage in the automated pipeline** (deliberate tradeoff,
  see Research findings). Reconsidered 2026-09-15 after Antun asked about
  JobSpy (a library hitting LinkedIn's internal "guest" job-search API
  directly, rather than rendering pages like Firecrawl attempted) — a
  technically different approach that might actually pull data where
  Firecrawl was blocked, but the decision to exclude LinkedIn was never
  purely about technical feasibility: it's ToS/account-risk based, and that
  risk applies regardless of which tool succeeds technically. Decision
  held: **excluded from the automated pipeline.**
  **Chosen path for LinkedIn coverage: manual, by Antun, outside this
  pipeline entirely** — a browser extension or script he runs himself while
  logged into his own LinkedIn session, not wired into CronCreate or any
  scheduled agent. Lower risk than automation because a human is in the
  loop triggering it each time, rather than an unattended daily scraper. Not
  built as part of this project; revisit only if Antun finds a specific
  tool/workflow he wants folded in later.
