"""Hashing utilities for MCP Web Search.

CRITICAL: The ID computed here is for write-time upsert dedup only —
it must NEVER be used as a query key.
"""

import re
from hashlib import sha256


def normalize(text: str) -> str:
    r"""Normalize text by converting to lowercase, stripping punctuation, and collapsing whitespace.

    The sequence of operations:
    1. Convert to lowercase.
    2. Strip punctuation by replacing characters matching [^\w\s] with spaces.
    3. Collapse multiple whitespace characters into a single space and strip leading/trailing whitespace.
    """
    # 1. Convert to lowercase
    lowered = text.lower()
    # 2. Strip punctuation (replace non-word/non-space characters with a space)
    stripped = re.sub(r"[^\w\s]", " ", lowered)
    # 3. Collapse whitespace and strip
    collapsed = re.sub(r"\s+", " ", stripped).strip()
    return collapsed


def compute_id(
    simplified_query: str, framework_name: str, framework_version: str
) -> str:
    """Compute a deterministic 32-character ID for write-time upsert dedup.

    CRITICAL: This ID is for write-time upsert dedup only —
    it must NEVER be used as a query key.
    """
    normalized_query = normalize(simplified_query)
    combined = f"{normalized_query}\x1f{framework_name}\x1f{framework_version}"
    return sha256(combined.encode("utf-8")).hexdigest()[:32]
