"""Quiz Manager for Learnify"""
import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from claude_client import ClaudeClient
from prompt_templates import QuizPrompts

logger = logging.getLogger(__name__)

@dataclass
class QuizOption:
    id: str
    text: str
    is_correct: bool
    feedback: str
    understanding: str

@dataclass
class QuizQuestion:
    id: int
    question: str
    concept_tested: str
    options: list[QuizOption]

    def get_correct_option(self) -> Optional[QuizOption]:
        for option in self.options:
            if option.is_correct:
                return option
        return None

@dataclass
class QuizResult:
    question_id: int
    selected_option_id: str
    is_correct: bool
    feedback: str
    understanding: str
    concept_tested: str

@dataclass
class Quiz:
    topic: str
    questions: list[QuizQuestion]
    results: list[QuizResult] = field(default_factory=list)
    current_index: int = 0

    @property
    def score(self) -> int:
        return sum(1 for r in self.results if r.is_correct)

    @property
    def total(self) -> int:
        return len(self.questions)

    @property
    def percentage(self) -> float:
        return (self.score / self.total * 100) if self.total > 0 else 0

    @property
    def is_complete(self) -> bool:
        return len(self.results) == len(self.questions)

    def get_wrong_concepts(self) -> list[str]:
        return [r.concept_tested for r in self.results if not r.is_correct]

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "score": self.score,
            "total": self.total,
            "percentage": self.percentage,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "concept_tested": q.concept_tested,
                    "options": [
                        {"id": o.id, "text": o.text, "is_correct": o.is_correct,
                         "feedback": o.feedback, "understanding": o.understanding}
                        for o in q.options
                    ]
                }
                for q in self.questions
            ],
            "results": [
                {
                    "question_id": r.question_id,
                    "selected_option_id": r.selected_option_id,
                    "is_correct": r.is_correct,
                    "feedback": r.feedback,
                    "concept_tested": r.concept_tested
                }
                for r in self.results
            ]
        }


class QuizManager:
    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.client = claude_client or ClaudeClient()

    def generate_quiz(self, topic: str, teaching_content: str, num_questions: int = 4, difficulty: str = "intermediate") -> Quiz:
        logger.info(f"Generating quiz for: {topic}")
        response = self.client.generate_quiz(
            QuizPrompts.SYSTEM_PROMPT,
            QuizPrompts.get_quiz_prompt(topic, teaching_content, num_questions, difficulty)
        )
        return self._parse_quiz_response(topic, response)

    def _parse_quiz_response(self, topic: str, response: str) -> Quiz:
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1])

            data = json.loads(clean_response)
            questions = []

            for q_data in data.get("questions", []):
                options = [
                    QuizOption(
                        id=o["id"],
                        text=o["text"],
                        is_correct=o["is_correct"],
                        feedback=o["feedback"],
                        understanding=o["understanding"]
                    )
                    for o in q_data.get("options", [])
                ]
                question = QuizQuestion(
                    id=q_data["id"],
                    question=q_data["question"],
                    concept_tested=q_data.get("concept_tested", "General understanding"),
                    options=options
                )
                questions.append(question)

            return Quiz(topic=topic, questions=questions)
        except Exception as e:
            logger.error(f"Failed to parse quiz: {e}")
            raise ValueError(f"Failed to parse quiz response: {e}")

    def submit_answer(self, quiz: Quiz, question_id: int, selected_option_id: str) -> QuizResult:
        question = next((q for q in quiz.questions if q.id == question_id), None)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        selected_option = next((o for o in question.options if o.id == selected_option_id), None)
        if not selected_option:
            raise ValueError(f"Option {selected_option_id} not found")

        result = QuizResult(
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=selected_option.is_correct,
            feedback=selected_option.feedback,
            understanding=selected_option.understanding,
            concept_tested=question.concept_tested
        )
        quiz.results.append(result)
        quiz.current_index += 1
        return result

    def get_performance_analysis(self, quiz: Quiz) -> dict:
        correct_concepts = [r.concept_tested for r in quiz.results if r.is_correct]
        incorrect_concepts = [r.concept_tested for r in quiz.results if not r.is_correct]

        strengths = []
        if quiz.percentage >= 75:
            strengths.append("Strong overall understanding")
        if correct_concepts:
            strengths.append(f"Good grasp of: {', '.join(correct_concepts[:2])}")

        weaknesses = [f"Review: {c}" for c in incorrect_concepts]

        if quiz.percentage >= 80:
            recommendations = ["Excellent! Ready for advanced topics", "Try teaching this to reinforce learning"]
        elif quiz.percentage >= 60:
            recommendations = ["Good progress! Review missed concepts", "Practice with real-world applications"]
        else:
            recommendations = ["Re-read the teaching material", "Focus on fundamentals first"]

        return {
            "score": quiz.score,
            "total": quiz.total,
            "percentage": quiz.percentage,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations
        }
