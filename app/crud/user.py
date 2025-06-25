from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserCreate
from app.crud.base import CRUDBase # Assuming you have a base CRUD class

class CRUDUser(CRUDBase[User, UserCreate, None]): # No update schema for now
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, user_in: UserCreate) -> User:
        db_user = User(email=user_in.email, hashed_password=user_in.password) 
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

user_crud = CRUDUser(User)