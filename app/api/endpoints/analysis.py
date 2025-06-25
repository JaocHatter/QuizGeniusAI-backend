from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import StatusResponse
from app.schemas.subtopic import SubtopicAnalysisResult, FlashcardSchema, QuestionSchema, QuizDataResponse
from app.crud.subtopic import subtopic_crud
from typing import List

router = APIRouter()

@router.get("/{subtopic_id}/status", response_model=StatusResponse)
def get_analysis_status(subtopic_id: int, db: Session = Depends(get_db)):
    """
    Consulta el estado de una tarea de análisis.
    """
    db_subtopic = subtopic_crud.get(db, id=subtopic_id)
    if not db_subtopic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")
    
    return StatusResponse(status=db_subtopic.status, message=db_subtopic.title)


@router.get("/{subtopic_id}/result", response_model=SubtopicAnalysisResult)
def get_analysis_result(subtopic_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el resultado completo de un análisis una vez que ha terminado.
    """
    db_subtopic = subtopic_crud.get(db, id=subtopic_id)

    if not db_subtopic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")
    
    if db_subtopic.status == "PROCESSING":
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail="Analysis is still in progress. Please wait.")
    
    if db_subtopic.status == "FAILED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Analysis failed. Error: {db_subtopic.error_message}")
        
    if db_subtopic.status != "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analysis is not in a completed state.")

    # Construir la respuesta final a partir de los datos en la BD
    all_generated_flashcards: List[FlashcardSchema] = []
    for fc in db_subtopic.flashcards:
        all_generated_flashcards.append(FlashcardSchema(id=fc.id, front=fc.front, back=fc.back))

    all_generated_quizzes_data: List[QuizDataResponse] = []
    for db_quiz in db_subtopic.quizzes:
        questions_for_quiz: List[QuestionSchema] = []
        for db_question in db_quiz.questions:
            options_list = db_question.options.split(",")
            questions_for_quiz.append(QuestionSchema(
                id=db_question.id,
                question=db_question.question_text,
                options=options_list,
                correctAnswer=db_question.correct_answer_index,
                explanation=db_question.explanation
            ))
        all_generated_quizzes_data.append(QuizDataResponse(
            id=str(db_quiz.id),
            title=db_quiz.title,
            description=db_quiz.description,
            difficulty=db_quiz.difficulty,
            questions=questions_for_quiz
        ))

    key_concepts = db_subtopic.key_concepts or []

    return SubtopicAnalysisResult(
        subtopic_id=db_subtopic.id,
        subtopic_title=db_subtopic.title,
        key_concepts=key_concepts,
        flashcards_generated=all_generated_flashcards,
        quizzes_generated=all_generated_quizzes_data
    )
