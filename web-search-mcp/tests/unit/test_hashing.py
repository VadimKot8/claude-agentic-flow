import pytest
from mcp_web_search.utils.hashing import normalize, compute_id


def test_normalize_lowercase():
    assert normalize("HELLO WORLD") == "hello world"


def test_normalize_punctuation():
    # punctuation replaced by space, then collapsed
    assert normalize("hello, world!!!") == "hello world"
    assert normalize("abc#def$ghi") == "abc def ghi"


def test_normalize_whitespace():
    assert normalize("  hello   world  ") == "hello world"


def test_normalize_order_preservation():
    # "Hello,   World!" -> "hello,   world!" -> "hello    world " -> "hello world"
    assert normalize("Hello,   World!") == "hello world"


def test_compute_id_length_and_format():
    h = compute_id("test query", "react", "18.2.0")
    assert len(h) == 32
    # must be hex
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_id_determinism():
    h1 = compute_id("test query", "react", "18.2.0")
    h2 = compute_id("test query", "react", "18.2.0")
    assert h1 == h2


def test_compute_id_normalization():
    h1 = compute_id("  Test  Query! ", "react", "18.2.0")
    h2 = compute_id("test query", "react", "18.2.0")
    assert h1 == h2


def test_compute_id_normalization_equivalence():
    h1 = compute_id("How to instantiate agent.", "react", "18.2.0")
    h2 = compute_id("how to instantiate agent", "react", "18.2.0")
    assert h1 == h2


def test_compute_id_different():
    h1 = compute_id("test query", "react", "18.2.0")
    h2 = compute_id("test query 2", "react", "18.2.0")
    h3 = compute_id("test query", "vue", "18.2.0")
    h4 = compute_id("test query", "react", "19.0.0")
    assert len({h1, h2, h3, h4}) == 4
