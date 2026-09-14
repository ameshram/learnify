"""Tests for security utilities — sanitization, validation, rate limiting."""
from security import (
    RateLimiter,
    sanitize_input,
    validate_difficulty,
    validate_topic,
)


def test_sanitize_input_preserves_ampersand_and_quotes():
    # sanitize no longer HTML-escapes, so legitimate text is preserved verbatim
    # (e.g. 'R&D'); validate_topic() is the layer that rejects unsafe characters.
    assert sanitize_input("R&D in AI/ML") == "R&D in AI/ML"
    assert "'" in sanitize_input("it's fine")


def test_sanitize_input_strips_control_characters():
    assert sanitize_input("hello\x00\x07world") == "helloworld"


def test_sanitize_input_truncates_to_max_length():
    result = sanitize_input("x" * 500, max_length=50)
    assert len(result) == 50


def test_sanitize_input_collapses_whitespace_and_strips():
    assert sanitize_input("  hello    world  ") == "hello world"


def test_sanitize_input_empty():
    assert sanitize_input("") == ""


def test_validate_topic():
    assert validate_topic("Photosynthesis")[0] is True
    assert validate_topic("")[0] is False        # required
    assert validate_topic("a")[0] is False        # too short
    assert validate_topic("x" * 201)[0] is False  # too long
    assert validate_topic("bad<topic>")[0] is False  # invalid characters


def test_validate_difficulty():
    for good in ("beginner", "intermediate", "advanced"):
        assert validate_difficulty(good)[0] is True
    assert validate_difficulty("expert")[0] is False


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(requests_per_minute=2)
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is False   # 3rd within the window
    assert limiter.is_allowed("client-2") is True     # a different client is unaffected


def test_rate_limiter_remaining():
    limiter = RateLimiter(requests_per_minute=3)
    limiter.is_allowed("c")
    assert limiter.get_remaining("c") == 2
