from sqlalchemy.orm import Session
from app.db.models import Workspace, User, Subtopic
from app.schemas.workspace import WorkspaceCreate
from app.crud.base import CRUDBase

class CRUDWorkspace(CRUDBase[Workspace, WorkspaceCreate, None]):
    def create_with_owner(self, db: Session, obj_in: WorkspaceCreate, owner_id: int) -> Workspace:
        db_obj = Workspace(**obj_in.model_dump(), owner_id=owner_id)
        db.add(db_obj)  
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_user_workspaces(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Workspace]:
        return db.query(Workspace).filter(Workspace.owner_id == user_id).offset(skip).limit(limit).all()

workspace_crud = CRUDWorkspace(Workspace)