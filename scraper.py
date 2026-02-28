"""
Letterboxd diary scraper.

Fetches all diary entries for a public Letterboxd profile, including
film name, rating, watched date, and tags.

HTML structure notes (Letterboxd as of early 2025 — selectors may need
tweaking if they update their markup):
  - Diary listing:   /{username}/films/diary/page/{n}/
  - Entry rows:      tr.diary-entry-row
  - Rating class:    .rating.rated-N  where N/2 = star rating (1–10 → 0.5–5 ★)
  - Tags:            May appear in the listing row, or only on the per-date page
  - Per-date page:   /{username}/films/diary/for/YYYY/MM/DD/
"""

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://letterboxd.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 0.5  # seconds between requests — be polite


@dataclass
class DiaryEntry:
    title: str
    year: Optional[str] = None
    rating: Optional[float] = None
    date: Optional[str] = None  # "YYYY-MM-DD"
    tags: list = field(default_factory=list)
    rewatch: bool = False
    slug: Optional[str] = None  # film URL slug


# ── low-level helpers ──────────────────────────────────────────────────────────

def _fetch(url: str) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except Exception:
        pass
    return None


def _parse_rating(el) -> Optional[float]:
    """Convert a Letterboxd rating element to a float (0.5 – 5.0)."""
    if el is None:
        return None
    for cls in el.get("class", []):
        m = re.match(r"rated-(\d+)$", cls)
        if m:
            return int(m.group(1)) / 2
    return None


def _parse_tags(row) -> list[str]:
    """
    Try several selectors to find tags in a diary row.
    Letterboxd renders tags differently depending on context.
    """
    selectors = [
        ".td-tags a",
        ".diary-entry-row .tags a",
        ".tags a",
        "a[href*='/tag/']",
    ]
    for sel in selectors:
        els = row.select(sel)
        tags = [e.get_text(strip=True) for e in els if e.get_text(strip=True)]
        if tags:
            return tags
    return []


# ── page-level scrapers ────────────────────────────────────────────────────────

def _scrape_listing_page(username: str, page: int) -> tuple[list[DiaryEntry], bool]:
    """Scrape one paginated diary listing page. Returns (entries, has_next)."""
    soup = _fetch(f"{BASE_URL}/{username}/films/diary/page/{page}/")
    if soup is None:
        return [], False

    entries = []
    for row in soup.select("tr.diary-entry-row"):
        e = DiaryEntry(title="")

        # Film title and slug
        title_a = row.select_one(".td-film h3 a, .td-film .headline-3 a")
        if title_a:
            e.title = title_a.get_text(strip=True)
            m = re.search(r"/film/([^/]+)/", title_a.get("href", ""))
            if m:
                e.slug = m.group(1)

        # Release year
        yr_el = row.select_one(".td-released .number, .td-released span")
        if yr_el:
            e.year = yr_el.get_text(strip=True)

        # Star rating
        e.rating = _parse_rating(row.select_one(".td-rating .rating"))

        # Watched date — extracted from the day-cell link href
        # e.g. /username/films/diary/for/2024/02/28/
        day_a = row.select_one(".td-day a")
        if day_a:
            m = re.search(r"/for/(\d{4})/(\d{2})/(\d{2})/", day_a.get("href", ""))
            if m:
                e.date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

        # Rewatch flag
        e.rewatch = bool(
            row.select_one(".td-rewatch .icon-rewatch, .td-rewatch.-active")
        )

        # Tags (may be empty here; deep scan fills these in later)
        e.tags = _parse_tags(row)

        if e.title:
            entries.append(e)

    has_next = soup.select_one(".paginate-nextprev a.next") is not None
    return entries, has_next


def _scrape_date_page_tags(
    username: str, date: str, slug: Optional[str]
) -> list[str]:
    """
    Fetch tags from the per-date diary page, e.g.:
      /username/films/diary/for/2024/02/28/

    If multiple films were watched that day, match by slug.
    """
    if not date:
        return []
    year, month, day = date.split("-")
    url = f"{BASE_URL}/{username}/films/diary/for/{year}/{month}/{day}/"
    soup = _fetch(url)
    if soup is None:
        return []

    for row in soup.select("tr.diary-entry-row"):
        # If we know the slug, only match the right film
        if slug:
            title_a = row.select_one(".td-film h3 a, .td-film .headline-3 a")
            if title_a and slug not in title_a.get("href", ""):
                continue
        tags = _parse_tags(row)
        if tags:
            return tags
        # Even if no tags found, return empty for this match
        if slug:
            return []

    return []


# ── public API ─────────────────────────────────────────────────────────────────

def scrape_user(
    username: str,
    on_progress: Optional[Callable[[str, Optional[float]], None]] = None,
    deep_scan: bool = False,
) -> list[DiaryEntry]:
    """
    Scrape all diary entries for a public Letterboxd profile.

    Args:
        username:     Letterboxd username.
        on_progress:  Optional callback(message, fraction_0_to_1).
                      fraction is None during the listing phase.
        deep_scan:    If True, visit each per-date page to fetch tags that
                      aren't visible on the diary listing (slower).

    Returns:
        List of DiaryEntry objects, empty if user not found / profile private.
    """
    all_entries: list[DiaryEntry] = []
    page = 1

    # ── Phase 1: scrape paginated diary listing ────────────────────────────────
    while True:
        if on_progress:
            on_progress(f"Fetching diary page {page}…", None)

        entries, has_next = _scrape_listing_page(username, page)

        if not entries and page == 1:
            return []  # user doesn't exist or profile is private

        all_entries.extend(entries)

        if not has_next:
            break

        page += 1
        time.sleep(DELAY)

    # ── Phase 2 (optional): visit date pages to fill in missing tags ───────────
    if deep_scan:
        needs_tags = [e for e in all_entries if not e.tags and e.date]
        total = len(needs_tags)

        for i, entry in enumerate(needs_tags):
            if on_progress:
                on_progress(
                    f"Fetching tags for '{entry.title}' ({i + 1}/{total})…",
                    (i + 1) / total,
                )
            entry.tags = _scrape_date_page_tags(username, entry.date, entry.slug)
            time.sleep(DELAY)

    return all_entries
