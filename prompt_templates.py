"""Prompt Templates for Learnify"""

class TeachingPrompts:
    SYSTEM_PROMPT = """You are an expert educator and teaching assistant. Your role is to explain concepts clearly and engagingly.

TEACHING PRINCIPLES:
1. Start with foundations before advancing to complex ideas
2. Use real-world analogies that connect to everyday experiences
3. Include concrete examples that illustrate abstract concepts
4. Break down complex topics into digestible sections
5. Use clear, accessible language appropriate to the difficulty level

OUTPUT FORMAT:
- Use Markdown formatting for structure
- Include clear section headings with ##
- Use bullet points for key concepts
- Include code blocks with syntax highlighting when relevant
- Add blockquotes for important definitions"""

    @staticmethod
    def get_teaching_prompt(topic: str, difficulty: str = "intermediate") -> str:
        difficulty_guide = {
            "beginner": "Use simple vocabulary, multiple analogies, no assumed prior knowledge.",
            "intermediate": "Balance theory and practice, include some technical depth.",
            "advanced": "In-depth technical explanations, edge cases, best practices."
        }
        return f"""Please teach me about: **{topic}**

Difficulty Level: {difficulty.upper()}
{difficulty_guide.get(difficulty, difficulty_guide["intermediate"])}

Structure your response with:
1. **Introduction** - What this topic is and why it matters
2. **Core Concepts** - The fundamental ideas with analogies
3. **How It Works** - Detailed explanation
4. **Real-World Examples** - Practical applications
5. **Key Takeaways** - Summary of important points

Make it engaging, clear, and educational. Use Markdown formatting."""


class QuizPrompts:
    SYSTEM_PROMPT = """You are an expert educational assessment designer. Create quiz questions that test understanding.

OUTPUT FORMAT - Return ONLY valid JSON:
{
  "questions": [
    {
      "id": 1,
      "question": "Question text?",
      "concept_tested": "What this tests",
      "options": [
        {"id": "A", "text": "Option text", "is_correct": false, "feedback": "Why wrong", "understanding": "What this reveals"},
        {"id": "B", "text": "Option text", "is_correct": true, "feedback": "Why correct", "understanding": "What this shows"},
        {"id": "C", "text": "Option text", "is_correct": false, "feedback": "Why wrong", "understanding": "What this reveals"},
        {"id": "D", "text": "Option text", "is_correct": false, "feedback": "Why wrong", "understanding": "What this reveals"}
      ]
    }
  ]
}

Return ONLY the JSON, no other text."""

    @staticmethod
    def get_quiz_prompt(topic: str, teaching_content: str, num_questions: int = 4, difficulty: str = "intermediate") -> str:
        return f"""Based on this teaching content about "{topic}", create {num_questions} multiple choice questions.

TEACHING CONTENT:
{teaching_content[:3000]}

REQUIREMENTS:
- Generate exactly {num_questions} questions
- Difficulty: {difficulty}
- Each question must have exactly 4 options (A, B, C, D)
- Only ONE correct answer per question
- Include detailed feedback for every option

Return ONLY the JSON object."""


class InsightsPrompts:
    SYSTEM_PROMPT = """You are a learning analytics expert who provides personalized feedback and study recommendations. Be encouraging but honest, specific and actionable."""

    @staticmethod
    def get_insights_prompt(topic: str, score: int, total: int, wrong_answers: list) -> str:
        percentage = (score / total * 100) if total > 0 else 0
        wrong_list = "\n".join([f"- {c}" for c in wrong_answers]) if wrong_answers else "None"
        return f"""Provide personalized learning insights:

Topic: {topic}
Score: {score}/{total} ({percentage:.0f}%)

Concepts struggled with:
{wrong_list}

Provide:
1. **Performance Summary** (2-3 encouraging sentences)
2. **Strengths** (what they demonstrated understanding of)
3. **Areas to Review** (specific concepts to revisit)
4. **Next Steps** (2-3 actionable recommendations)
5. **Encouragement** (motivating closing message)

Use Markdown formatting."""
