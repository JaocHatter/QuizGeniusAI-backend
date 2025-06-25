from sqlalchemy.orm import Session
from app.db.models import User
from app.crud.user import user_crud
from app.schemas.user import UserCreate, UserResponse, UserProgress
from app.crud.workspace import workspace_crud
from app.crud.subtopic import subtopic_crud

class UserService:
    def create_user(self, db: Session, user_in: UserCreate) -> User:
        return user_crud.create_user(db, user_in)

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return user_crud.get_by_email(db, email)

    def get_user_progress(self, db: Session, user_id: int) -> UserProgress:
        workspaces = workspace_crud.get_user_workspaces(db, user_id)
        uploaded_materials_data = []
        quizzes_data = []
        flashcards_data = []

        for workspace in workspaces:
            subtopics = subtopic_crud.get_subtopics_by_workspace(db, workspace.id)
            for subtopic in subtopics:
                uploaded_materials_data.append({
                    "id": subtopic.id,
                    "title": subtopic.title,
                    "original_filename": subtopic.original_filename,
                    "created_at": subtopic.created_at,
                    "progress": subtopic.progress,
                })
                # Fetch quizzes and flashcards for detailed progress
                quizzes = subtopic_crud.get_subtopic_quizzes(db, subtopic.id)
                for quiz in quizzes:
                    quizzes_data.append({
                        "id": quiz.id,
                        "title": quiz.title,
                        "description": quiz.description,
                        "questions": len(quiz.questions),
                        "completedAt": quiz.completed_at,
                        "score": quiz.score,
                        "difficulty": quiz.difficulty,
                        "timeSpent": quiz.time_spent_minutes,
                    })
                
                flashcards = subtopic_crud.get_subtopic_flashcards(db, subtopic.id)
                flashcards_data.append({
                    "id": subtopic.id, # Using subtopic ID for the set
                    "title": subtopic.title,
                    "cards": len(flashcards),
                    "lastStudied": subtopic.last_studied,
                    "progress": subtopic.progress,
                })

        return UserProgress(
            quizzes=quizzes_data,
            flashcards=flashcards_data,
            uploaded_materials=uploaded_materials_data
        )

user_service = UserService()