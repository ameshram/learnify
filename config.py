"""Learnify Configuration"""
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'claude-sonnet-4-20250514')
    MAX_TOKENS_TEACHING = int(os.getenv('MAX_TOKENS_TEACHING', 4096))
    MAX_TOKENS_QUIZ = int(os.getenv('MAX_TOKENS_QUIZ', 2048))
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///learnify.db')

def get_config():
    return Config
