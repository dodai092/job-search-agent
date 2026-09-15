#!/usr/bin/env python3
"""Pull job postings from Remotive's public API. See SPEC.md Sources.

Note: category/search query params are ignored by the free endpoint (always
returns the same ~15 jobs) — pulled unfiltered, downstream stages filter.
"""

import json
import sys
import urllib.request

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


def pull_all() -> dict:
    """Returns {"postings": [...], "status": "ok"|"failed", "error": str|None}."""
    try:
        req = urllib.request.Request(REMOTIVE_URL, headers={"User-Agent": "job-search-agent"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception as e:
        return {"postings": [], "status": "failed", "error": str(e)}

    postings = [
        {
            "title": j.get("title", ""),
            "description": j.get("description", ""),
            "link": j.get("url", ""),
            "employer": j.get("company_name", ""),
            "candidate_required_location": j.get("candidate_required_location", ""),
            "category": j.get("category", ""),
            "source": "remotive",
        }
        for j in data.get("jobs", [])
    ]
    return {"postings": postings, "status": "ok", "error": None}


if __name__ == "__main__":
    result = pull_all()
    print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stdout)
    print(f"\npulled: {len(result['postings'])}, status: {result['status']}", file=sys.stderr)
