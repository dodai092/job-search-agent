#!/usr/bin/env python3
"""Pull job postings from Jobicy's public API. See SPEC.md Sources.

industry= filtering is confirmed working (unlike Remotive/MojPosao). Slugs
pulled live from the API's own ?get=industries rather than hardcoded, per
Jobicy's own documented recommendation.
"""

import json
import sys
import urllib.request

JOBICY_URL = "https://jobicy.com/api/v2/remote-jobs"

# Relevant to criteria.yaml target_roles: Software Engineering, DevOps &
# Infrastructure, Data Science & Analytics.
INDUSTRIES = ["engineering", "admin", "data-science"]


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "job-search-agent"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def pull_industry(slug: str, count: int = 50) -> list[dict]:
    data = fetch(f"{JOBICY_URL}?count={count}&industry={slug}")
    return [
        {
            "title": j.get("jobTitle", ""),
            "description": j.get("jobDescription", ""),
            "link": j.get("url", ""),
            "employer": j.get("companyName", ""),
            # Real geographic eligibility per posting — see SPEC.md Sources.
            "job_geo": j.get("jobGeo", ""),
            "source": "jobicy",
        }
        for j in data.get("jobs", [])
    ]


def pull_all() -> dict:
    """Returns {"postings": [...], "status": "ok"|"failed", "error": str|None}."""
    all_postings = []
    for slug in INDUSTRIES:
        try:
            all_postings.extend(pull_industry(slug))
        except Exception as e:
            return {"postings": all_postings, "status": "failed", "error": f"{slug}: {e}"}
    return {"postings": all_postings, "status": "ok", "error": None}


if __name__ == "__main__":
    result = pull_all()
    print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stdout)
    print(f"\npulled: {len(result['postings'])}, status: {result['status']}", file=sys.stderr)
