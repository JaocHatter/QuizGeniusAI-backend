from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SubtopicBase(BaseModel):
    title: str
    description: Optional[str] = None

class SubtopicCreate(SubtopicBase):
    workspace_id: int
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    status: Optional[str] = "PROCESSING"  

class SubtopicResponse(SubtopicBase):
    id: int
    workspace_id: int
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime
    last_studied: Optional[datetime] = None
    progress: float
    cards_count: int
    questions_count: int
    key_concepts: Optional[List[str]] = None
    status: str = "PROCESSING"
    class Config:
        from_attributes = True

class FlashcardSchema(BaseModel):
    id: int
    front: str
    back: str

class FlashcardSetResponse(BaseModel):
    id: str 
    title: str 
    cards: List[FlashcardSchema]

class SubtopicFlashcardSet(BaseModel):
    id: int
    title: str
    cards: int
    last_studied: Optional[datetime] = None
    progress: float

class QuestionSchema(BaseModel):
    id: int
    question: str
    options: List[str]
    correctAnswer: int
    explanation: Optional[str] = None

class QuizDataResponse(BaseModel):
    id: str 
    title: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    questions: List[QuestionSchema]

class SubtopicQuizResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    questions: int
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    difficulty: Optional[str] = None
    time_spent: Optional[float] = None 

class SubtopicAnalysisResult(BaseModel):
    subtopic_id: int
    subtopic_title: str
    key_concepts: List[str] 
    flashcards_generated: List[FlashcardSchema]
    quizzes_generated: List[QuizDataResponse] 

class SubtopicInfoResponse(BaseModel):
    subtopic_id: int
    subtopic_title: str
    key_concepts: List[str]
    flashcards_count: int
    quizzes_count: int