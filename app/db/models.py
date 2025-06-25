from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): 
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspaces = relationship("Workspace", back_populates="owner")

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="workspaces")
    subtopics = relationship("Subtopic", back_populates="workspace")

class Subtopic(Base):
    __tablename__ = "subtopics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True) 
    content_summary = Column(Text, nullable=True)  
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    original_filename = Column(String, nullable=True) 
    file_path = Column(String, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)
    last_studied = Column(DateTime, nullable=True)
    progress = Column(Float, default=0.0)
    cards_count = Column(Integer, default=0) 
    questions_count = Column(Integer, default=0) 
    status = Column(String, default="pending")  
    key_concepts = Column(Text, nullable=True)

    workspace = relationship("Workspace", back_populates="subtopics")
    flashcards = relationship("Flashcard", back_populates="subtopic")
    quizzes = relationship("Quiz", back_populates="subtopic")

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True, index=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    subtopic_id = Column(Integer, ForeignKey("subtopics.id"))

    subtopic = relationship("Subtopic", back_populates="flashcards")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String, nullable=True) 
    subtopic_id = Column(Integer, ForeignKey("subtopics.id"))
    completed_at = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)
    time_spent_minutes = Column(Float, nullable=True) 

    subtopic = relationship("Subtopic", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  
    correct_answer_index = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))

    quiz = relationship("Quiz", back_populates="questions")