"""Helpers for safely building PostgREST text filters.

Supabase/PostgREST treats commas, parentheses and operators inside ``or_`` and
``ilike`` expressions as filter syntax. User-supplied search text must never be
interpolated raw, otherwise a crafted search can inject extra filters.
"""

from __future__ import annotations

import re

_ALLOWED = re.compile(r"[^A-Za-z0-9\s@.+\-&']")
_WHITESPACE = re.compile(r"\s+")


def sanitize_search_term(value: object, max_length: int = 80) -> str:
    """Return a filter-safe, length-limited search term.

    Keeps letters, numbers, spaces and a small set of useful punctuation
    (email/phone/company characters). Everything PostgREST treats as syntax is
    removed.
    """
    if not isinstance(value, str):
        return ""

    term = value.strip()[:max_length]
    term = _ALLOWED.sub(" ", term)
    term = _WHITESPACE.sub(" ", term).strip()
    return term
