"""Session Manager for Learnify"""
import json
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_config

logger = logging.getLogger(__name__)
Base = declarative_base()


class LearningSession(Base):
    __tablename__ = 'learning_sessions'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    topic = Column(String(256), nullable=False)
    difficulty = Column(String(32), default='intermediate')
    teaching_content = Column(Text)
    quiz_data = Column(Text)
    score = Column(Integer)
    total_questions = Column(Integer)
    percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': self.percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class SessionManager:
    def __init__(self, database_url: Optional[str] = None):
        config = get_config()
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_session(self, session_id: str, topic: str, difficulty: str = "intermediate") -> LearningSession:
        db = self.Session()
        try:
            session = LearningSession(
                session_id=session_id,
                topic=topic,
                difficulty=difficulty
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()

    def get_session(self, session_id: str) -> Optional[LearningSession]:
        db = self.Session()
        try:
            return db.query(LearningSession).filter_by(session_id=session_id).first()
        finally:
            db.close()

    def update_teaching_content(self, session_id: str, content: str) -> None:
        db = self.Session()
        try:
            session = db.query(LearningSession).filter_by(session_id=session_id).first()
            if session:
                session.teaching_content = content
                db.commit()
        finally:
            db.close()

    def update_quiz_results(self, session_id: str, quiz_data: dict, score: int, total: int) -> None:
        db = self.Session()
        try:
            session = db.query(LearningSession).filter_by(session_id=session_id).first()
            if session:
                session.quiz_data = json.dumps(quiz_data)
                session.score = score
                session.total_questions = total
                session.percentage = (score / total * 100) if total > 0 else 0
                session.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    def get_history(self, limit: int = 20) -> list:
        db = self.Session()
        try:
            sessions = db.query(LearningSession).order_by(
                LearningSession.created_at.desc()
            ).limit(limit).all()
            return [s.to_dict() for s in sessions]
        finally:
            db.close()

    def get_stats(self) -> dict:
        db = self.Session()
        try:
            total_sessions = db.query(LearningSession).count()
            completed = db.query(LearningSession).filter(
                LearningSession.completed_at.isnot(None)
            ).all()

            avg_score = 0
            if completed:
                scores = [s.percentage for s in completed if s.percentage is not None]
                avg_score = sum(scores) / len(scores) if scores else 0

            topics = db.query(LearningSession.topic).distinct().count()

            return {
                'total_sessions': total_sessions,
                'completed_sessions': len(completed),
                'average_score': round(avg_score, 1),
                'unique_topics': topics
            }
        finally:
            db.close()
