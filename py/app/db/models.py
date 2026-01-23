"""Database models using SQLAlchemy."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("TopicProgress", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("ExerciseSubmission", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, default=dict)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Exercise(Base):
    """Exercise model."""
    __tablename__ = "exercises"

    id = Column(String, primary_key=True, default=generate_uuid)
    subject = Column(String, nullable=False)  # math, physics, chemistry
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # beginner, intermediate, advanced
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text)
    type = Column(String, nullable=False)  # mcq, short_answer, proof
    extra_data = Column(JSON, default=dict)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    submissions = relationship("ExerciseSubmission", back_populates="exercise", cascade="all, delete-orphan")


class ExerciseSubmission(Base):
    """Exercise submission model."""
    __tablename__ = "exercise_submissions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(String, ForeignKey("exercises.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    score = Column(Float)
    feedback = Column(JSON, default=dict)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="submissions")
    exercise = relationship("Exercise", back_populates="submissions")


class TopicProgress(Base):
    """Topic progress tracking model."""
    __tablename__ = "topic_progress"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)  # math, physics, chemistry
    topic = Column(String, nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0
    attempts = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    last_practiced = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="progress")


class GradingResult(Base):
    """Grading result model."""
    __tablename__ = "grading_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    questions = Column(JSON, nullable=False)
    answers = Column(JSON, nullable=False)
    scores = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=False)
    feedback = Column(Text)
    suggestions = Column(JSON, default=list)
    graded_at = Column(DateTime, default=datetime.utcnow)
