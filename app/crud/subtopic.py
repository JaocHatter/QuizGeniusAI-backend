from sqlalchemy.orm import Session
from app.db.models import Subtopic, Flashcard, Quiz, Question
from app.schemas.subtopic import SubtopicCreate, FlashcardSchema, QuestionSchema
from app.crud.base import CRUDBase
from typing import List, Optional

class CRUDSubtopic(CRUDBase[Subtopic, SubtopicCreate, None]):

    def get_subtopics_by_workspace(self, db: Session, workspace_id: int) -> List[Subtopic]:
        return db.query(Subtopic).filter(Subtopic.workspace_id == workspace_id).all()

    def create_subtopic_with_content(
        self,
        db: Session,
        obj_in: SubtopicCreate,
        flashcards: List[FlashcardSchema],
        quizzes_data: List[dict] 
    ) -> Subtopic:
        db_subtopic = Subtopic(**obj_in.model_dump())
        db_subtopic.cards_count = len(flashcards)
        db_subtopic.questions_count = sum(len(quiz_data.get("questions", [])) for quiz_data in quizzes_data)

        db.add(db_subtopic)
        db.flush() 

        for fc_data in flashcards:
            db_flashcard = Flashcard(
                front=fc_data.front,
                back=fc_data.back,
                subtopic_id=db_subtopic.id
            )
            db.add(db_flashcard)

        for quiz_data in quizzes_data:
            db_quiz = Quiz(
                title=quiz_data.get("title"),
                description=quiz_data.get("description"),
                difficulty=quiz_data.get("difficulty"),
                subtopic_id=db_subtopic.id
            )
            db.add(db_quiz)
            db.flush() 

            for q_data in quiz_data.get("questions", []):
                db_question = Question(
                    question_text=q_data.get("question"),
                    options=",".join(q_data.get("options", [])), 
                    correct_answer_index=q_data.get("correctAnswer"),
                    explanation=q_data.get("explanation"),
                    quiz_id=db_quiz.id
                )
                db.add(db_question)

        db.commit()
        db.refresh(db_subtopic)
        return db_subtopic

    def get_subtopic_flashcards(self, db: Session, subtopic_id: int) -> List[Flashcard]:
        return db.query(Flashcard).filter(Flashcard.subtopic_id == subtopic_id).all()

    def get_subtopic_quizzes(self, db: Session, subtopic_id: int) -> List[Quiz]:
        return db.query(Quiz).filter(Quiz.subtopic_id == subtopic_id).all()

    def count_subtopic_flashcards(self, db: Session, subtopic_id: int) -> int:
        return db.query(Flashcard).filter(Flashcard.subtopic_id == subtopic_id).count()

    def count_subtopic_quizzes(self, db: Session, subtopic_id: int) -> int:
        return db.query(Quiz).filter(Quiz.subtopic_id == subtopic_id).count()
    
    def get_quiz_with_questions(self, db: Session, quiz_id: int) -> Optional[Quiz]:
        return db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def update_with_content(
        self,
        db: Session,
        subtopic_id: int,
        title: str,
        description: str,
        key_concepts, 
        flashcards: List[dict],
        quizzes_data: List[dict],
        status="COMPLETED",
    ) -> Subtopic:
        db_subtopic = db.query(Subtopic).filter(Subtopic.id == subtopic_id).first()
        if not db_subtopic:
            return None

        # Eliminar flashcards y quizzes existentes
        db.query(Flashcard).filter(Flashcard.subtopic_id == subtopic_id).delete()
        db.query(Quiz).filter(Quiz.subtopic_id == subtopic_id).delete()

        # Actualizar contadores y estado
        db_subtopic.title = title
        db_subtopic.description = description
        db_subtopic.key_concepts = key_concepts
        db_subtopic.cards_count = len(flashcards)
        db_subtopic.questions_count = sum(len(quiz_data.get("questions", [])) for quiz_data in quizzes_data)
        db_subtopic.status = status

        # Crear nuevos flashcards
        for fc_data in flashcards:
            db_flashcard = Flashcard(
                front=fc_data["front"],
                back=fc_data["back"],
                subtopic_id=subtopic_id
            )
            db.add(db_flashcard)

        # Crear nuevos quizzes y preguntas
        for quiz_data in quizzes_data:
            db_quiz = Quiz(
                title=quiz_data.get("title"),
                description=quiz_data.get("description"),
                difficulty=quiz_data.get("difficulty"),
                subtopic_id=subtopic_id
            )
            db.add(db_quiz)
            db.flush()

            for q_data in quiz_data.get("questions", []):
                db_question = Question(
                    question_text=q_data.get("question_text"),
                    options=",".join(q_data.get("options", [])),
                    correct_answer_index=q_data.get("correct_answer_index"),
                    explanation=q_data.get("explanation"),
                    quiz_id=db_quiz.id
                )
                db.add(db_question)

        db.commit()
        db.refresh(db_subtopic)
        return db_subtopic

    def update_status(
        self,
        db: Session,
        subtopic_id: int,
        status: str
    ) -> Subtopic:
        db_subtopic = db.query(Subtopic).filter(Subtopic.id == subtopic_id).first()
        if not db_subtopic:
            return None
            
        db_subtopic.status = status
        db.commit()
        db.refresh(db_subtopic)
        return db_subtopic


subtopic_crud = CRUDSubtopic(Subtopic)