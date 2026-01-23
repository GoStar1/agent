"""Pydantic schemas for exercise API."""
from pydantic import BaseModel
from typing import List, Optional


class ExerciseGenerateRequest(BaseModel):
    """Exercise generation request schema."""
    subject: str  # math, physics, chemistry
    topic: Optional[str] = None
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    count: int = 3
    type: str = "short_answer"  # mcq, short_answer, proof


class Exercise(BaseModel):
    """Exercise schema."""
    id: Optional[str] = None
    question: str
    type: str
    answer: Optional[str] = None
    explanation: Optional[str] = None
    knowledge_points: Optional[List[str]] = None


class ExerciseGenerateResponse(BaseModel):
    """Exercise generation response schema."""
    exercises: List[Exercise]


class ExerciseSubmitRequest(BaseModel):
    """Exercise submission request schema."""
    user_id: str
    exercise_id: str
    answer: str


class ExerciseSubmitResponse(BaseModel):
    """Exercise submission response schema."""
    score: float
    feedback: str
    correct_answer: Optional[str] = None
