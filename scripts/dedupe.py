#!/usr/bin/env python3
"""Dedupe new postings against what's already known. See SPEC.md Reliability."""

from urllib.parse import urlparse


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.netloc.lower()}{path.lower()}"


def normalize_title_company(title: str, company: str) -> tuple[str, str]:
    return (title.strip().lower(), (company or "").strip().lower())


def dedupe(
    postings: list[dict],
    existing_urls: set[str],
    existing_title_company: set[tuple[str, str]],
) -> list[dict]:
    """Returns postings not already present in existing_urls/existing_title_company,
    and not duplicated against each other within this batch."""
    seen_urls = set(existing_urls)
    seen_title_company = set(existing_title_company)
    new_postings = []

    for p in postings:
        norm_url = normalize_url(p.get("link"))
        if norm_url:
            if norm_url in seen_urls:
                continue
            seen_urls.add(norm_url)
        else:
            key = normalize_title_company(p.get("title", ""), p.get("employer", ""))
            if key in seen_title_company:
                continue
            seen_title_company.add(key)
        new_postings.append(p)

    return new_postings


if __name__ == "__main__":
    # Self-test against the cases called out in SPEC.md Reliability.
    postings = [
        {"title": "AI Developer", "link": "https://posao.hr/oglasi/ai-developer/123/?utm_source=x"},
        {"title": "AI Developer", "link": "https://posao.hr/oglasi/ai-developer/123/"},  # same, diff tracking param
        {"title": "VIŠI/A AISTENT/ICA", "employer": "INSTITUT ZA FIZIKU", "link": None},
        {"title": "VIŠI/A AISTENT/ICA", "employer": "INSTITUT ZA FIZIKU", "link": None},  # dup within batch
        {"title": "Senior PHP Developer", "link": "https://europa.eu/some-other-job"},
    ]
    result = dedupe(postings, existing_urls=set(), existing_title_company=set())
    assert len(result) == 3, f"expected 3 unique postings, got {len(result)}: {result}"

    # Existing-in-sheet cases.
    existing_urls = {normalize_url("https://posao.hr/oglasi/ai-developer/123/")}
    existing_title_company = {normalize_title_company("VIŠI/A AISTENT/ICA", "INSTITUT ZA FIZIKU")}
    result2 = dedupe(postings, existing_urls, existing_title_company)
    assert len(result2) == 1, f"expected 1 (only the PHP posting), got {len(result2)}: {result2}"

    print("dedupe.py self-test passed")
