#!/usr/bin/env python3
"""Conservative hard filters. See SPEC.md Matching — only exclude on strong,
unambiguous signals; everything ambiguous passes through to fit-scoring
(task 7). A wrong exclusion here is silent and unrecoverable; a wrong LLM
score is visible and correctable, so we bias toward passing more through.
"""

import re

# Title-based seniority exclusion — only exact, unambiguous junior/intern signals.
JUNIOR_INTERN_PATTERN = re.compile(
    r"\b(junior|intern(ship)?|pripravnik(a|ca)?|praksa)\b", re.IGNORECASE
)

# Geo fields (Jobicy job_geo, Remotive candidate_required_location) that
# explicitly name a single country/region clearly incompatible with hiring
# from Croatia, with no EU/Europe/Worldwide qualifier anywhere in the string.
INCOMPATIBLE_GEO_PATTERN = re.compile(
    r"^(usa|us|united states|canada|australia|new zealand|latam|uk only|united kingdom)$",
    re.IGNORECASE,
)
COMPATIBLE_GEO_HINTS = re.compile(
    r"(europe|worldwide|anywhere|eu\b|croatia|hr\b)", re.IGNORECASE
)


def check_posting(p: dict) -> str | None:
    """Returns a rejection reason string, or None if the posting passes."""
    title = p.get("title", "")
    if JUNIOR_INTERN_PATTERN.search(title):
        return "junior/intern title keyword"

    geo = p.get("job_geo") or p.get("candidate_required_location") or ""
    geo = geo.strip()
    if geo and not COMPATIBLE_GEO_HINTS.search(geo):
        # Only reject if geo names something explicit and clearly incompatible —
        # not just "no compatible hint" (that's the common ambiguous case, e.g.
        # a single unfamiliar city name — pass those through, don't guess).
        for part in re.split(r",\s*", geo):
            if INCOMPATIBLE_GEO_PATTERN.match(part.strip()):
                return f"geo restricted to: {geo}"

    return None


def apply_hard_filters(postings: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (passed, rejected). Each rejected item has a 'reject_reason' key."""
    passed, rejected = [], []
    for p in postings:
        reason = check_posting(p)
        if reason:
            p = {**p, "reject_reason": reason}
            rejected.append(p)
        else:
            passed.append(p)
    return passed, rejected


if __name__ == "__main__":
    postings = [
        {"title": "Junior Frontend Developer"},
        {"title": "Pripravnik za IT podršku"},
        {"title": "Senior PHP Developer", "job_geo": "USA"},
        {"title": "AI Automation Engineer", "job_geo": "Europe"},
        {"title": "Backend Developer", "candidate_required_location": "Worldwide"},
        {"title": "Data Scientist", "job_geo": "Canada"},
        {"title": "AI Consultant"},  # no geo field at all — pass through
        {"title": "Web Developer", "job_geo": "Berlin, Germany"},  # ambiguous city — pass through
    ]
    passed, rejected = apply_hard_filters(postings)
    # Rejected: Junior Frontend Developer, Pripravnik, Senior PHP Dev (geo=USA), Data Scientist (geo=Canada)
    assert len(rejected) == 4, f"expected 4 rejected, got {len(rejected)}: {rejected}"
    # Passed: AI Automation Engineer (Europe), Backend Developer (Worldwide), AI Consultant (no geo), Web Developer (Berlin — ambiguous city, no confident match either way)
    assert len(passed) == 4, f"expected 4 passed, got {len(passed)}: {passed}"
    print("hard_filter.py self-test passed")
    print(f"passed: {len(passed)}, rejected: {len(rejected)}")
