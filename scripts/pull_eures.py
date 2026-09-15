#!/usr/bin/env python3
"""Pull job postings from the EURES public search API. See SPEC.md Sources.

Note: specificSearchCode must be "TITLE", not the docs' example "EVERYWHERE" —
EVERYWHERE was confirmed in the feasibility spike to barely filter results.
"""

import json
import sys
import urllib.request

EURES_URL = "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search"

# Derived from criteria.yaml target_roles.
KEYWORDS = ["AI Developer", "AI Automation Engineer", "AI Consultant", "Web Developer"]


def search_keyword(keyword: str, results_per_page: int = 25) -> list[dict]:
    payload = {
        "resultsPerPage": results_per_page,
        "page": 1,
        "sortSearch": "MOST_RECENT",
        "keywords": [{"keyword": keyword, "specificSearchCode": "TITLE"}],
        "publicationPeriod": None,
        "occupationUris": [],
        "skillUris": [],
        "requiredExperienceCodes": [],
        "positionScheduleCodes": [],
        "sectorCodes": [],
        "educationAndQualificationLevelCodes": [],
        "positionOfferingCodes": [],
        "locationCodes": ["hr-NS"],
        "euresFlagCodes": [],
        "otherBenefitsCodes": [],
        "requiredLanguages": [],
        "minNumberPost": None,
        "sessionId": "job-search-agent",
        "userPreferredLanguage": None,
        "requestLanguage": "en",
    }
    req = urllib.request.Request(
        EURES_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)

    postings = []
    for jv in data.get("jvs", []):
        postings.append(
            {
                "title": jv.get("title", ""),
                "description": jv.get("description", ""),
                # EURES's API has no link/URL field on job vacancy objects (confirmed
                # against the full schema) and no working detail-page URL pattern was
                # found (tested candidate URLs — real vs. fake IDs rendered identical
                # generic SPA shells). No link is included; see SPEC.md Sources.
                "link": None,
                "employer": (jv.get("employer") or {}).get("name", ""),
                "locations": list((jv.get("locationMap") or {}).keys()),
                "source": "eures",
            }
        )
    return postings


def pull_all() -> dict:
    """Returns {"postings": [...], "status": "ok"|"failed", "error": str|None}."""
    all_postings = []
    for kw in KEYWORDS:
        try:
            all_postings.extend(search_keyword(kw))
        except Exception as e:
            return {"postings": all_postings, "status": "failed", "error": f"{kw}: {e}"}
    return {"postings": all_postings, "status": "ok", "error": None}


if __name__ == "__main__":
    result = pull_all()
    print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stdout)
    print(f"\npulled: {len(result['postings'])}, status: {result['status']}", file=sys.stderr)
