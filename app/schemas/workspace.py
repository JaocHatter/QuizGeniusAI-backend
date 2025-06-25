from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class WorkspaceBase(BaseModel):
    title: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True