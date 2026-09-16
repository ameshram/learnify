"""Tests for prompt_templates - pure prompt construction, no API calls."""
from prompt_templates import InsightsPrompts, QuizPrompts, TeachingPrompts


def test_teaching_prompt_includes_topic_and_is_nonempty():
    prompt = TeachingPrompts.get_teaching_prompt("photosynthesis", "beginner")
    assert "photosynthesis" in prompt
    assert len(prompt) > 100
    assert TeachingPrompts.SYSTEM_PROMPT  # non-empty system prompt


def test_teaching_prompt_difficulty_context_differs():
    beginner = TeachingPrompts.get_teaching_prompt("x", "beginner")
    advanced = TeachingPrompts.get_teaching_prompt("x", "advanced")
    assert beginner != advanced
    assert "beginner" in beginner.lower()


def test_teaching_prompt_unknown_difficulty_falls_back_to_intermediate():
    unknown = TeachingPrompts.get_teaching_prompt("x", "wizard")
    intermediate = TeachingPrompts.get_teaching_prompt("x", "intermediate")
    assert unknown == intermediate


def test_quiz_prompt_truncates_teaching_content_to_3000_chars():
    content = "HEAD_MARKER " + ("x" * 4000) + " TAIL_MARKER"  # tail sits past char 3000
    prompt = QuizPrompts.get_quiz_prompt("topic", content, num_questions=5)
    assert "HEAD_MARKER" in prompt
    assert "TAIL_MARKER" not in prompt
    assert "5" in prompt
    assert "topic" in prompt


def test_insights_prompt_handles_zero_total_without_dividing_by_zero():
    prompt = InsightsPrompts.get_insights_prompt("topic", 0, 0, [])
    assert "0%" in prompt
    assert "None" in prompt  # no wrong answers -> "None"


def test_insights_prompt_percentage_and_wrong_list():
    prompt = InsightsPrompts.get_insights_prompt("topic", 3, 4, ["recursion", "closures"])
    assert "75%" in prompt
    assert "recursion" in prompt
    assert "closures" in prompt
