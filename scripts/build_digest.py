#!/usr/bin/env python3
"""Build the daily digest email content. See SPEC.md Output/Reliability.
Deterministic decision + formatting logic only — the actual send happens via
the Gmail MCP at runtime, not from this script (same pattern as fit-scoring:
the scheduled agent already has that capability, no need to duplicate it).

Sends as HTML, not plain text: a plain-text test send showed Gmail
auto-linkifying bare domain-like text (e.g. "posao.hr" in the run summary)
into fake tracking-redirect links. HTML output puts real <a href> only on
actual job links, so nothing else gets auto-linkified.
"""

from html import escape


def build_digest(new_matches: list[dict], run_summary: dict, failures: list[str]) -> dict:
    """new_matches: rows already written to the Sheet this run (title, company,
    source, link, fit_score). run_summary: per-source {pulled, deduped_out,
    hard_filtered_out, scored_below_threshold, added} counts. failures: source
    names that failed to pull this run (or failed 2+ consecutive days — see
    SPEC.md Reliability; the caller decides which failures qualify).

    Returns {"should_send": bool, "subject": str, "body": str, "html_body": str}.
    "body" is a plain-text fallback; send html_body as the actual email body.
    """
    should_send = bool(new_matches) or bool(failures)
    if not should_send:
        return {"should_send": False, "subject": "", "body": "", "html_body": ""}

    subject_parts = []
    if new_matches:
        subject_parts.append(f"{len(new_matches)} new job match{'es' if len(new_matches) != 1 else ''}")
    if failures:
        subject_parts.append(f"{len(failures)} source issue{'s' if len(failures) != 1 else ''}")
    subject = "Job search digest: " + ", ".join(subject_parts)

    text_lines = []
    html_lines = []

    if failures:
        text_lines.append("Sources that failed to pull today:")
        html_lines.append("<p><strong>Sources that failed to pull today:</strong></p><ul>")
        for f in failures:
            text_lines.append(f"  - {f}")
            html_lines.append(f"<li>{escape(f)}</li>")
        html_lines.append("</ul>")
        text_lines.append("")

    if new_matches:
        text_lines.append(f"{len(new_matches)} new match(es):")
        html_lines.append(f"<p><strong>{len(new_matches)} new match(es):</strong></p><ul>")
        for m in new_matches:
            title = escape(m.get("title", ""))
            company = escape(m.get("company", "?"))
            source = escape(m.get("source", "?"))
            score = escape(str(m.get("fit_score", "?")))
            link = m.get("link")

            text_link = link or "(no link for this source — search the title manually)"
            text_lines.append(f"- [{score}/10] {m.get('title', '')} @ {m.get('company', '?')} ({m.get('source', '?')})")
            text_lines.append(f"  {text_link}")

            if link:
                html_lines.append(f'<li>[{score}/10] <a href="{escape(link)}">{title}</a> @ {company} ({source})</li>')
            else:
                html_lines.append(f"<li>[{score}/10] {title} @ {company} ({source}) — no link, search the title manually</li>")
        html_lines.append("</ul>")
        text_lines.append("")
    else:
        text_lines.append("No new matches today.")
        html_lines.append("<p>No new matches today.</p>")
        text_lines.append("")

    if run_summary:
        text_lines.append("Run summary:")
        html_lines.append("<p><strong>Run summary:</strong></p><ul>")
        for source, counts in run_summary.items():
            summary_line = (
                f"pulled {counts.get('pulled', 0)}, "
                f"deduped out {counts.get('deduped_out', 0)}, "
                f"hard-filtered out {counts.get('hard_filtered_out', 0)}, "
                f"scored below threshold {counts.get('scored_below_threshold', 0)}, "
                f"added {counts.get('added', 0)}"
            )
            text_lines.append(f"  {source}: {summary_line}")
            html_lines.append(f"<li>{escape(source)}: {escape(summary_line)}</li>")
        html_lines.append("</ul>")

    return {
        "should_send": True,
        "subject": subject,
        "body": "\n".join(text_lines),
        "html_body": "\n".join(html_lines),
    }


if __name__ == "__main__":
    # No new matches, no failures — should not send.
    result = build_digest([], {}, [])
    assert result["should_send"] is False, result

    # Matches only.
    matches = [{"title": "AI Automation Engineer", "company": "TestCo", "source": "jobicy",
                "link": "https://example.com/job/1", "fit_score": 8}]
    summary = {"posao.hr": {"pulled": 30, "deduped_out": 5, "hard_filtered_out": 20, "scored_below_threshold": 4, "added": 1}}
    result = build_digest(matches, summary, [])
    assert result["should_send"] is True
    assert "1 new job match" in result["subject"]
    assert "AI Automation Engineer" in result["body"]
    assert "posao.hr" in result["body"]
    assert '<a href="https://example.com/job/1">AI Automation Engineer</a>' in result["html_body"]
    # Source name must NOT be inside an anchor tag (that was the bug).
    assert "<a" not in result["html_body"].split("Run summary")[1]

    # Failures only, no matches.
    result = build_digest([], {}, ["eures"])
    assert result["should_send"] is True
    assert "1 source issue" in result["subject"]
    assert "eures" in result["body"]
    assert "No new matches today." in result["body"]

    # Link-less posting (EURES) formats gracefully, no anchor tag.
    matches_no_link = [{"title": "Senior PHP Developer", "company": "FER PROJEKT", "source": "eures",
                         "link": None, "fit_score": 6}]
    result = build_digest(matches_no_link, {}, [])
    assert "search the title manually" in result["body"]
    assert "<a" not in result["html_body"]

    print("build_digest.py self-test passed")
