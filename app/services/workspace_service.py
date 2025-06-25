from sqlalchemy.orm import Session
from app.db.models import Workspace
from app.crud.workspace import workspace_crud
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

class WorkspaceService:
    def create_workspace(self, db: Session, workspace_in: WorkspaceCreate, owner_id: int) -> Workspace:
        return workspace_crud.create_with_owner(db, workspace_in, owner_id)

    def get_workspaces_for_user(self, db: Session, user_id: int) -> list[Workspace]:
        return workspace_crud.get_user_workspaces(db, user_id)

    def get_workspace(self, db: Session, workspace_id: int) -> Workspace | None:
        return workspace_crud.get(db, workspace_id)
    
workspace_service = WorkspaceService()