"""Tests for quiz scoring and analysis - pure logic, no API calls.

QuizManager is constructed with a dummy client so no ANTHROPIC_API_KEY or real
ClaudeClient is needed; the methods under test never touch the client.
"""
import pytest

from quiz_manager import Quiz, QuizManager, QuizOption, QuizQuestion


def _make_quiz():
    q1 = QuizQuestion(
        id=1,
        question="Q1?",
        concept_tested="concept-a",
        options=[
            QuizOption(id="A", text="a", is_correct=True, feedback="correct", understanding="u"),
            QuizOption(id="B", text="b", is_correct=False, feedback="wrong", understanding="u"),
        ],
    )
    q2 = QuizQuestion(
        id=2,
        question="Q2?",
        concept_tested="concept-b",
        options=[
            QuizOption(id="A", text="a", is_correct=False, feedback="wrong", understanding="u"),
            QuizOption(id="B", text="b", is_correct=True, feedback="correct", understanding="u"),
        ],
    )
    return Quiz(topic="Topic", questions=[q1, q2])


def test_get_correct_option():
    quiz = _make_quiz()
    assert quiz.questions[0].get_correct_option().id == "A"
    assert quiz.questions[1].get_correct_option().id == "B"


def test_empty_quiz_percentage_is_zero():
    quiz = Quiz(topic="Empty", questions=[])
    assert quiz.total == 0
    assert quiz.percentage == 0
    assert quiz.is_complete is True  # 0 results == 0 questions


def test_scoring_and_completion():
    quiz = _make_quiz()
    mgr = QuizManager(claude_client=object())  # dummy - no ClaudeClient constructed

    assert quiz.total == 2
    assert quiz.score == 0
    assert quiz.is_complete is False

    r1 = mgr.submit_answer(quiz, 1, "A")   # correct
    assert r1.is_correct is True
    assert quiz.score == 1
    assert quiz.current_index == 1

    r2 = mgr.submit_answer(quiz, 2, "A")   # wrong (correct is B)
    assert r2.is_correct is False
    assert quiz.score == 1
    assert quiz.is_complete is True
    assert quiz.percentage == 50.0
    assert quiz.get_wrong_concepts() == ["concept-b"]


def test_submit_answer_invalid_question_or_option():
    quiz = _make_quiz()
    mgr = QuizManager(claude_client=object())
    with pytest.raises(ValueError):
        mgr.submit_answer(quiz, 999, "A")
    with pytest.raises(ValueError):
        mgr.submit_answer(quiz, 1, "Z")


def test_performance_analysis():
    quiz = _make_quiz()
    mgr = QuizManager(claude_client=object())
    mgr.submit_answer(quiz, 1, "A")   # correct: concept-a
    mgr.submit_answer(quiz, 2, "A")   # wrong: concept-b

    analysis = mgr.get_performance_analysis(quiz)
    assert analysis["score"] == 1
    assert analysis["total"] == 2
    assert analysis["percentage"] == 50.0
    assert any("concept-b" in w for w in analysis["weaknesses"])
    assert analysis["recommendations"]  # non-empty


# --- _parse_quiz_response: the brittle model-output parsing path -----------

_ONE_Q = ('{"questions":[{"id":1,"question":"Q?","concept_tested":"c","options":['
          '{"id":"A","text":"a","is_correct":true,"feedback":"f","understanding":"u"},'
          '{"id":"B","text":"b","is_correct":false,"feedback":"f","understanding":"u"}]}]}')


def test_parse_quiz_response_clean_json():
    mgr = QuizManager(claude_client=object())
    quiz = mgr._parse_quiz_response("topic", _ONE_Q)
    assert quiz.total == 1
    assert quiz.questions[0].get_correct_option().id == "A"


def test_parse_quiz_response_json_fenced():
    mgr = QuizManager(claude_client=object())
    quiz = mgr._parse_quiz_response("topic", f"```json\n{_ONE_Q}\n```")
    assert quiz.total == 1


def test_parse_quiz_response_plain_fenced():
    mgr = QuizManager(claude_client=object())
    quiz = mgr._parse_quiz_response("topic", f"```\n{_ONE_Q}\n```")
    assert quiz.total == 1


def test_parse_quiz_response_invalid_json_raises_valueerror():
    mgr = QuizManager(claude_client=object())
    with pytest.raises(ValueError):
        mgr._parse_quiz_response("topic", "this is not json at all")


def test_parse_quiz_response_missing_keys_raises_valueerror():
    mgr = QuizManager(claude_client=object())
    with pytest.raises(ValueError):
        mgr._parse_quiz_response("topic", '{"questions":[{"id":1}]}')
