#!/usr/bin/env python3
"""Append matched postings to the Sheet via the Apps Script Web App.
See apps-script/DEPLOY.md — requires the deployment URL, not yet set.
"""

import json
import os
import sys
import urllib.request

# Set after deploying apps-script/Code.gs (see apps-script/DEPLOY.md).
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby-SlsiZ15Cfa961xtKs0afNPoKrvsXEyTr-niudrf5t-LOROgfSxG5u3HGBFPiheNjaQ/exec"
# Not hardcoded — this is a credential, kept out of the git repo. Set via
# the SHEET_APPEND_SECRET env var (the daily cloud routine's prompt supplies
# it directly, not committed anywhere). See apps-script/DEPLOY.md.
SHARED_SECRET = os.environ.get("SHEET_APPEND_SECRET")


def append_rows(rows: list[dict]) -> dict:
    """Each row: title, company, location, source, link, fit_score, rationale,
    date_found, status. Returns {"ok": bool, "appended"|"error": ...}."""
    if not APPS_SCRIPT_URL:
        return {"ok": False, "error": "APPS_SCRIPT_URL not set — deploy apps-script/Code.gs first"}
    if not SHARED_SECRET:
        return {"ok": False, "error": "SHEET_APPEND_SECRET env var not set"}

    payload = {"secret": SHARED_SECRET, "action": "append_rows", "rows": rows}
    req = urllib.request.Request(
        APPS_SCRIPT_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    if not APPS_SCRIPT_URL:
        print("APPS_SCRIPT_URL not set yet — deploy apps-script/Code.gs first (see DEPLOY.md)", file=sys.stderr)
        sys.exit(1)
    result = append_rows([{"title": "Test Row", "company": "Test", "source": "manual-test"}])
    print(json.dumps(result, indent=2))
