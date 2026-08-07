"""
Deterministic, rule-based mock parser for POST /tasks/quick-add.
Simulates what an LLM response would contain — zero network calls, zero
API keys. Any two correct implementations of this exact algorithm must
produce identical output for a given input.
"""

import re

# Group (i): any match -> priority "high" (wins over group ii if both present)
PRIORITY_HIGH_KEYWORDS = ["urgent", "asap"]
# Group (ii): any match (and no group i match) -> priority "low"
PRIORITY_LOW_KEYWORDS = ["whenever", "low priority"]

# Due-date keywords/phrases, checked in this exact order — first match wins.
DATE_KEYWORDS_ORDERED = [
    "today",
    "tomorrow",
    "next week",
    "next monday", "next tuesday", "next wednesday", "next thursday",
    "next friday", "next saturday", "next sunday",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]


def parse_description(description):
    """
    Returns {"title": str, "priority": "low"|"medium"|"high", "due_date_hint": str|None}
    """
    lower_desc = description.lower()

    # --- Priority (step b) ---
    has_high = any(kw in lower_desc for kw in PRIORITY_HIGH_KEYWORDS)
    has_low = any(kw in lower_desc for kw in PRIORITY_LOW_KEYWORDS)

    if has_high:
        priority = "high"
    elif has_low:
        priority = "low"
    else:
        priority = "medium"

    # Every group (i)/(ii) keyword actually present gets stripped from the
    # title, regardless of which one decided priority (title-stripping note).
    matched_priority_keywords = [
        kw for kw in (PRIORITY_HIGH_KEYWORDS + PRIORITY_LOW_KEYWORDS)
        if kw in lower_desc
    ]

    # --- Due-date hint (step c) — first match in the ordered list wins ---
    due_date_hint = None
    for kw in DATE_KEYWORDS_ORDERED:
        if kw in lower_desc:
            due_date_hint = kw
            break

    # --- Title (step d) ---
    title = description  # original-cased, untouched until now

    for kw in matched_priority_keywords:
        title = re.sub(re.escape(kw), "", title, flags=re.IGNORECASE)

    if due_date_hint:
        title = re.sub(re.escape(due_date_hint), "", title, flags=re.IGNORECASE)

    # Collapse any whitespace left behind by removed spans, then trim ends.
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        title = "Untitled task"

    return {"title": title, "priority": priority, "due_date_hint": due_date_hint}