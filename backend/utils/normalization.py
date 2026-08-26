"""String normalization, registration range matching, and text matching utilities."""

import re
from typing import Any, List, Optional, Set

STOP_WORDS = {
    "who", "is", "where", "what", "which", "the", "a", "an", "in", "at", "to", "for",
    "of", "and", "or", "on", "can", "i", "my", "me", "you", "your", "are", "do", "does",
    "have", "has", "get", "go", "reach", "take", "find", "meet", "sit", "located",
    "there", "near", "by", "from", "with", "tell", "show", "give", "please", "sir", "madam"
}


def normalize_text(text: Optional[str]) -> str:
    """Clean and standardize whitespace and case for matching."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip()).lower()


def normalize_room(room: Optional[str]) -> str:
    """Normalize room string while preserving verbatim identifier as sourced."""
    if not room:
        return ""
    return str(room).strip()


def parse_registration_number(reg_no: Optional[str]) -> Optional[str]:
    """Standardize registration number (uppercase, stripped)."""
    if not reg_no:
        return None
    cleaned = re.sub(r"[\s\-_]", "", str(reg_no).strip()).upper()
    return cleaned if cleaned else None


def is_reg_in_range(reg_no: str, start: Optional[str], end: Optional[str]) -> bool:
    """
    Check if a registration number falls within [start, end] range.
    Handles alphanumeric series comparison (e.g. 241FA04001 <= 241FA04015 <= 241FA04030).
    """
    if not reg_no:
        return False
    norm_reg = parse_registration_number(reg_no)
    if not norm_reg:
        return False

    norm_start = parse_registration_number(start) if start else None
    norm_end = parse_registration_number(end) if end else None

    if norm_start and norm_end:
        return norm_start <= norm_reg <= norm_end
    elif norm_start:
        return norm_reg >= norm_start
    elif norm_end:
        return norm_reg <= norm_end

    return False


def get_tokens(text: Optional[str], filter_stop_words: bool = True) -> Set[str]:
    """Extract lowercase search tokens with plural/singular variants, filtering out stop words."""
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", normalize_text(text))
    tokens = set()
    for word in cleaned.split():
        if len(word) >= 2:
            if filter_stop_words and word in STOP_WORDS:
                continue
            tokens.add(word)
            if word.endswith("s") and len(word) > 3:
                tokens.add(word[:-1])
            if word.endswith("es") and len(word) > 4:
                tokens.add(word[:-2])
            if word.endswith("ing") and len(word) > 4:
                tokens.add(word[:-3])
    return tokens


def calculate_match_score(query: str, target_fields: List[Optional[str]]) -> int:
    """
    Calculate flexible match score between a user query and multiple target fields.
    Handles substrings, reverse containment, acronyms, and token overlap without false positives from stop words.
    """
    norm_query = normalize_text(query)
    if not norm_query:
        return 1

    query_tokens = get_tokens(norm_query, filter_stop_words=True)
    if not query_tokens:
        # Fallback to unfiltered tokens if query consists only of short words
        query_tokens = get_tokens(norm_query, filter_stop_words=False)

    score = 0

    for field in target_fields:
        if not field:
            continue
        norm_field = normalize_text(field)
        field_tokens = get_tokens(norm_field, filter_stop_words=True)

        # Exact match
        if norm_query == norm_field:
            score += 40

        # Direct containment (only if query is meaningful and not a stop word)
        if len(norm_query) >= 3 and norm_query not in STOP_WORDS:
            if norm_query in norm_field:
                score += 25
            elif norm_field in norm_query and len(norm_field) >= 3 and norm_field not in STOP_WORDS:
                score += 20

        # Acronym matching (e.g. DBMS matching Database Management Systems)
        acronym = "".join([w[0] for w in norm_field.split() if w and w not in STOP_WORDS])
        if acronym and len(acronym) >= 2 and (norm_query == acronym or acronym in query_tokens):
            score += 30

        # Common abbreviations
        common_abbrevs = {
            "dbms": "database management systems",
            "ds": "data structures",
            "dsa": "data structures",
            "ai": "artificial intelligence",
            "ml": "machine learning",
            "os": "operating systems",
            "admin": "administrative",
            "hod": "head of department",
            "tp": "training and placement",
            "cse": "computer science and engineering",
            "it": "information technology",
            "ece": "electronics and communication engineering",
            "eee": "electrical and electronics engineering",
            "mech": "mechanical engineering",
            "civil": "civil engineering",
        }
        for abbr, full in common_abbrevs.items():
            if abbr in query_tokens and (abbr in norm_field or full in norm_field):
                score += 25
            if abbr == norm_query and (abbr in norm_field or full in norm_field):
                score += 30

        # Meaningful token overlap
        overlap = query_tokens.intersection(field_tokens)
        score += len(overlap) * 12

    return score
