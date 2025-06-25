from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserProgress
from app.schemas.token import Token
from app.services.user_service import user_service
from app.schemas.common import MessageResponse
from app.core.security import get_password_hash    
from app.core.security import verify_password, create_access_token
from app.core.security import get_current_user 
from app.db.models import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user

@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_service.get_user_by_email(db, email=form_data.username) 
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_email(db, user_in.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    user_in_db = UserCreate(email = user_in.email,password= hashed_password)
    user = user_service.create_user(db, user_in_db)
    return user 

@router.get("/me/progress", response_model=UserProgress)
def get_user_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    progress = user_service.get_user_progress(db, user.id)
    return progress 