from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import AnalysisInitiatedResponse
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.schemas.subtopic import SubtopicInfoResponse, SubtopicQuizResponse, SubtopicFlashcardSet, FlashcardSetResponse, QuizDataResponse
from app.schemas.subtopic import QuestionSchema, FlashcardSchema
from app.services.workspace_service import workspace_service
from app.services.analysis_service import analysis_service
from typing import List
from app.core.security import get_current_user 
from app.db.models import User

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(workspace_in: WorkspaceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workspace = workspace_service.create_workspace(db, workspace_in, user.id)
    return workspace

@router.get("/", response_model=List[WorkspaceResponse])
def get_workspaces(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workspaces = workspace_service.get_workspaces_for_user(db, user.id)
    return workspaces

@router.get("/{workspace_id}", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) # Renombrado a current_user para mayor claridad
):
    workspace = workspace_service.get_workspace(db, workspace_id)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Workspace with id {workspace_id} not found"
        )
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to access this workspace"
        )

    return workspace

@router.post("/{workspace_id}/upload-document/", response_model=AnalysisInitiatedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document_for_analysis(
    workspace_id: int,
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user) 
):
    """
    Inicia el análisis de un documento PDF en segundo plano.
    
    Responde inmediatamente con un ID para rastrear el progreso.
    """
    workspace = workspace_service.get_workspace(db, workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or not owned by user")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported.")

    # 1. Leer el contenido del archivo en memoria ANTES de pasarlo a la tarea de fondo.
    # El objeto UploadFile no es seguro para pasar entre hilos/tareas.
    file_contents = await file.read()
    filename = file.filename

    # 2. Crear una entrada preliminar en la base de datos para obtener un ID.
    # Esto es crucial para poder rastrear el estado de la tarea.
    # Necesitarás una función en tu CRUD para esto.
    initial_subtopic = analysis_service.create_initial_subtopic(
        db=db, 
        workspace_id=workspace_id, 
        filename=filename
    )

    # 3. Añadir la tarea de procesamiento pesado al fondo.
    # Pasamos los datos necesarios como argumentos simples (bytes, strings, ints).
    background_tasks.add_task(
        analysis_service.process_document_background,
        db=db,
        file_contents=file_contents,
        filename=filename,
        workspace_id=workspace_id,
        subtopic_id=initial_subtopic.id # Pasamos el ID para que la tarea sepa qué registro actualizar
    )

    # 4. Devolver una respuesta inmediata al cliente.
    return AnalysisInitiatedResponse(
        message="Document analysis has been initiated.",
        subtopic_id=initial_subtopic.id,
        filename=filename
    )

@router.get("/{workspace_id}/subtopics", response_model=List[SubtopicInfoResponse])
def get_workspace_subtopics(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    workspace = workspace_service.get_workspace(db, workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or not owned by user")

    from app.crud.subtopic import subtopic_crud
    db_subtopics = subtopic_crud.get_subtopics_by_workspace(db, workspace_id)

    subtopic_sets = []
    for subtopic in db_subtopics:
        processed_concepts = []
        key_concepts_str = subtopic.key_concepts
        if key_concepts_str:
            cleaned_str = key_concepts_str.strip('{}')
            parts = cleaned_str.split(',')
            for part in parts:
                processed_concepts.append(part.strip().strip('"'))
        subtopic_sets.append(SubtopicInfoResponse(
            subtopic_id=subtopic.id,
            subtopic_title=subtopic.title,
            key_concepts= processed_concepts,
            flashcards_count = subtopic.cards_count,
            quizzes_count = subtopic.questions_count
        ))
    return subtopic_sets

@router.get("/subtopics/{subtopic_id}/flashcards", response_model=FlashcardSetResponse)
def get_subtopic_flashcards(
    subtopic_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 1. Añadir dependencia de usuario
):
    from app.crud.subtopic import subtopic_crud
    
    subtopic = subtopic_crud.get(db, subtopic_id)
    if not subtopic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtopic not found")

    workspace = workspace_service.get_workspace(db, subtopic.workspace_id)
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access these flashcards"
        )
        
    flashcards = subtopic_crud.get_subtopic_flashcards(db, subtopic_id)
    
    return FlashcardSetResponse(
        id=str(subtopic_id),
        title=subtopic.title,
        cards=[FlashcardSchema(id=fc.id, front=fc.front, back=fc.back) for fc in flashcards]
    )


@router.get("/subtopics/{subtopic_id}/quizzes", response_model=List[SubtopicQuizResponse])
def get_subtopic_quizzes(
    subtopic_id: int,   
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.crud.subtopic import subtopic_crud
    
    subtopic = subtopic_crud.get(db, subtopic_id)
    if not subtopic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtopic not found")

    workspace = workspace_service.get_workspace(db, subtopic.workspace_id)
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access these quizzes"
        )

    quizzes = subtopic_crud.get_subtopic_quizzes(db, subtopic_id)
    
    response_quizzes = []
    for quiz in quizzes:
        response_quizzes.append(SubtopicQuizResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            questions=len(quiz.questions),
            completed_at=quiz.completed_at,
            score=quiz.score,
            difficulty=quiz.difficulty,
            time_spent=quiz.time_spent_minutes
        ))
    return response_quizzes

@router.get("/quizzes/{quiz_id}", response_model=QuizDataResponse)
def get_quiz_details(
    quiz_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.crud.subtopic import subtopic_crud
    
    quiz = subtopic_crud.get_quiz_with_questions(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        
    workspace = workspace_service.get_workspace(db, quiz.subtopic.workspace_id)
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this quiz"
        )

    questions_data = []
    for question in quiz.questions:
        options_list = question.options.split(",") 
        questions_data.append(QuestionSchema(
            id=question.id,
            question=question.question_text,
            options=options_list,
            correctAnswer=question.correct_answer_index,
            explanation=question.explanation
        ))
    
    return QuizDataResponse(
        id=str(quiz.id),
        title=quiz.title,
        description=quiz.description,
        difficulty=quiz.difficulty,
        questions=questions_data
    )