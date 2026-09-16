"""Claude API Client for Learnify"""
import anthropic
from typing import Generator, Optional
import logging
from config import get_config

logger = logging.getLogger(__name__)

class ClaudeClient:
    def __init__(self, api_key: Optional[str] = None):
        config = get_config()
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.default_model = config.DEFAULT_MODEL
        self.max_tokens_teaching = config.MAX_TOKENS_TEACHING
        self.max_tokens_quiz = config.MAX_TOKENS_QUIZ
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def stream_teaching_content(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Generator[str, None, None]:
        # Errors are intentionally NOT swallowed here. On an API failure this
        # raises, so the caller (app.py: generate()) emits an SSE `error` event
        # and skips persisting the failure - otherwise an error string would be
        # saved as the "lesson" and the quiz generated from it.
        model = model or self.default_model
        logger.info(f"Streaming with model: {model}")
        with self.client.messages.stream(
            model=model,
            max_tokens=self.max_tokens_teaching,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text
            response = stream.get_final_message()
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

    def generate_quiz(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        model = model or self.default_model
        response = self.client.messages.create(
            model=model,
            max_tokens=self.max_tokens_quiz,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        return response.content[0].text

    def generate_insights(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        model = model or self.default_model
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return "Unable to generate insights at this time."

    def get_usage_stats(self) -> dict:
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens
        }
