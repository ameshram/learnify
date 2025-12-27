"""Security utilities for Learnify"""
import re
import html
import time
import logging
from functools import wraps
from collections import defaultdict
from flask import request, jsonify, g

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        self.requests[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        now = time.time()
        minute_ago = now - 60
        recent = [t for t in self.requests[client_id] if t > minute_ago]
        return max(0, self.requests_per_minute - len(recent))


rate_limiter = RateLimiter()


def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_id = request.remote_addr or 'unknown'
        if not rate_limiter.is_allowed(client_id):
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': 60
            }), 429
        return f(*args, **kwargs)
    return decorated


def sanitize_input(text: str, max_length: int = 1000) -> str:
    if not text:
        return ""
    text = text[:max_length]
    text = html.escape(text)
    text = re.sub(r'[<>"\']', '', text)
    text = ' '.join(text.split())
    return text.strip()


def validate_topic(topic: str) -> tuple[bool, str]:
    if not topic:
        return False, "Topic is required"
    if len(topic) < 2:
        return False, "Topic must be at least 2 characters"
    if len(topic) > 200:
        return False, "Topic must be less than 200 characters"
    if re.search(r'[<>{}[\]\\]', topic):
        return False, "Topic contains invalid characters"
    return True, ""


def validate_difficulty(difficulty: str) -> tuple[bool, str]:
    valid = ['beginner', 'intermediate', 'advanced']
    if difficulty not in valid:
        return False, f"Difficulty must be one of: {', '.join(valid)}"
    return True, ""


def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response
