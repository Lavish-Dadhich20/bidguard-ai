"""
Shared helpers for the newer BidGuard document extractors.

These helpers are intentionally deterministic. They do not invent values:
when a field cannot be located confidently, None is returned.
"""

import re
from typing import Optional


def clean_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\s*\n\s*", " ", value)
    value = re.sub(r"\s{2,}", " ", value)
    value = value.strip(" \t\r\n:|-")
    return value or None


def search_first(text: str, patterns, flags=re.IGNORECASE) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return clean_value(match.group(1))
    return None


def search_line_value(text: str, labels) -> Optional[str]:
    """
    Finds a value on the same line as one of the supplied labels.

    Matching is line-anchored so a generic label such as "Declaration" does
    not accidentally match the word "Declaration" inside a document title.
    Longer labels are checked first.
    """
    ordered_labels = sorted(labels, key=len, reverse=True)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        for label in ordered_labels:
            pattern = rf"^(?:\d{{1,2}}[.)]\s*)?{re.escape(label)}\s*[:\-]?\s*(.*)$"
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                value = clean_value(match.group(1))
                if value:
                    return value

    return None


def search_block_value(text: str, labels) -> Optional[str]:
    """
    Finds a value after a label and stops at the next numbered field, known
    label, or end of text. Works well with synthetic/form-style certificates.
    """
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = rf"(?:{label_pattern})\s*[:\-]?\s*(.+?)(?=\n\s*\d{{1,2}}[.)]\s|\n\s*[A-Za-z][A-Za-z /&()_-]{{1,60}}\s*[:\-]|\Z)"
    return search_first(text, [pattern], flags=re.IGNORECASE | re.DOTALL)


def search_numbered_value(text: str, number: int, label: str) -> Optional[str]:
    pattern = rf"{number}\.\s*{re.escape(label)}\s*[:\-]?\s*(.+?)(?=\n\s*\d{{1,2}}\.\s|\n\s*Note:|\Z)"
    return search_first(text, [pattern], flags=re.IGNORECASE | re.DOTALL)


def search_date(text: str, labels) -> Optional[str]:
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = rf"(?:{label_pattern})\s*[:\-]?\s*(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{4}})"
    return search_first(text, [pattern])


def normalize_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value)
    if not match:
        return clean_value(value)
    dd, mm, yyyy = match.groups()
    return f"{int(dd):02d}/{int(mm):02d}/{yyyy}"


def normalize_percentage(value: Optional[str]):
    if not value:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", value)
    if not match:
        return clean_value(value)
    number = float(match.group(1))
    return int(number) if number.is_integer() else number
