from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserProgress(BaseModel):
    quizzes: List[dict] 
    flashcards: List[dict] 
    uploaded_materials: List[dict] 

class UserResponse(UserInDB):
    progress: Optional[UserProgress] = None