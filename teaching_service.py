"""Teaching service for Learnify.

A thin wrapper around a single streaming Claude call: it turns a
(topic, difficulty) pair into a structured explanation and streams the tokens
back to the caller.

Deliberately NOT an "agent" - there is no tool use, planning, memory, or
multi-step control loop here, just one model call behind a small interface.
The name reflects that.
"""
import logging
from typing import Generator, Optional

from claude_client import ClaudeClient
from prompt_templates import TeachingPrompts

logger = logging.getLogger(__name__)


class TeachingService:
    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.client = claude_client or ClaudeClient()

    def teach(self, topic: str, difficulty: str = "intermediate") -> Generator[str, None, None]:
        logger.info(f"Teaching topic: {topic} at {difficulty} level")
        system_prompt = TeachingPrompts.SYSTEM_PROMPT
        user_prompt = TeachingPrompts.get_teaching_prompt(topic, difficulty)
        yield from self.client.stream_teaching_content(system_prompt, user_prompt)

    def get_usage_stats(self) -> dict:
        return self.client.get_usage_stats()
