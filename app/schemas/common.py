from pydantic import BaseModel
from typing import Optional

class MessageResponse(BaseModel):
    message: str

class AnalysisInitiatedResponse(BaseModel):
    message: str
    subtopic_id: int
    filename: str

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None