#!/usr/bin/env python3
"""Pull job postings from Posao.hr's category RSS feeds. See SPEC.md Sources."""

import sys
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = {
    "informatika-i-telekomunikacije": "https://www.posao.hr/rss/djelatnost/informatika-i-telekomunikacije/",
}


def pull_feed(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    postings = []
    for item in root.findall("./channel/item"):
        postings.append(
            {
                "title": item.findtext("title", "").strip(),
                "description": (item.findtext("description", "") or "").strip(),
                "link": item.findtext("link", "").strip(),
                "pub_date": item.findtext("pubDate", "").strip(),
                "source": "posao.hr",
            }
        )
    return postings


def pull_all() -> dict:
    """Returns {"postings": [...], "status": "ok"|"failed", "error": str|None}."""
    all_postings = []
    for name, url in FEEDS.items():
        try:
            all_postings.extend(pull_feed(url))
        except Exception as e:
            return {"postings": all_postings, "status": "failed", "error": f"{name}: {e}"}
    return {"postings": all_postings, "status": "ok", "error": None}


if __name__ == "__main__":
    import json

    result = pull_all()
    print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stdout)
    print(f"\npulled: {len(result['postings'])}, status: {result['status']}", file=sys.stderr)
