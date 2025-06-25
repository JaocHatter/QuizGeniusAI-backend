import os
import logging
from sqlalchemy.orm import Session
from app.helpers.gemini_orchestrator import analyze_pdf_for_study
from app.crud.subtopic import subtopic_crud
from app.schemas.subtopic import SubtopicCreate
from app.db.models import Subtopic
from typing import List, Dict, Any

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisService:
    
    def create_initial_subtopic(self, db: Session, workspace_id: int, filename: str) -> Subtopic:
        """
        Crea un registro de subtema inicial con estado 'PROCESSING'.
        """ 
        logger.info(f"Creating initial subtopic for file: {filename} in workspace: {workspace_id}")
        subtopic_schema = SubtopicCreate(
            title=f"Analizando: {filename}",
            description="El análisis del documento está en proceso...",
            workspace_id=workspace_id,
            original_filename=filename,
            status="PROCESSING"
        )
        db_subtopic = subtopic_crud.create(db, obj_in=subtopic_schema)
        logger.info(f"Created initial subtopic with ID: {db_subtopic.id}")
        return db_subtopic

    async def process_document_background(self, db: Session, file_contents: bytes, filename: str, workspace_id: int, subtopic_id: int):
        """
        Función de segundo plano que procesa el PDF, llama a Gemini y actualiza la BD.
        """
        logger.info(f"Starting background processing for subtopic_id={subtopic_id}, filename={filename}")
        
        try:
            logger.info(f"Verifying subtopic existence for ID: {subtopic_id}")
            db_subtopic = subtopic_crud.get(db, id=subtopic_id)
            if not db_subtopic:
                logger.error(f"Subtopic not found with id={subtopic_id}")
                return

            # 1. Verificar contenido del archivo
            logger.info(f"Checking file contents for {filename}. Size: {len(file_contents)} bytes")
            if len(file_contents) == 0:
                logger.error("File contents are empty")
                raise ValueError("Empty file contents")

            # 2. Llamar a Gemini
            logger.info(f"Sending PDF '{filename}' to Gemini for analysis...")
            try:
                gemini_response = await analyze_pdf_for_study(file_contents)
                logger.info(f"Successfully received Gemini analysis for subtopic_id={subtopic_id}")
                logger.debug(f"Gemini response structure: {list(gemini_response.keys())}")
            except Exception as gemini_error:
                logger.error(f"Gemini analysis failed: {str(gemini_error)}")
                raise

            # 3. Procesar respuesta
            logger.info("Processing Gemini response data")
            key_concepts = gemini_response.get("key_concepts", [])
            subtopics_data = gemini_response.get("subtopics", [])
            
            if not subtopics_data:
                logger.warning("No subtopics data received from Gemini")
            
            main_subtopic_title = f"Material: {filename}"
            main_subtopic_description = "Análisis completo del documento."
            
            aggregated_flashcards = []
            aggregated_quizzes_raw_data = []

            for subtopic_data in subtopics_data:
                main_subtopic_description += f"\n- {subtopic_data['title']}"
                aggregated_flashcards.extend(subtopic_data.get("flashcards", []))
                aggregated_quizzes_raw_data.extend(subtopic_data.get("quizzes", []))
            
            logger.info(f"Processed {len(aggregated_flashcards)} flashcards and {len(aggregated_quizzes_raw_data)} quizzes")

            # 4. Actualizar BD
            logger.info(f"Updating subtopic {subtopic_id} with processed content")
            subtopic_crud.update_with_content(
                db=db,
                subtopic_id=subtopic_id,
                title=main_subtopic_title,
                description=main_subtopic_description,
                key_concepts=key_concepts,
                flashcards=aggregated_flashcards,
                quizzes_data=aggregated_quizzes_raw_data,
                status="COMPLETED"  
            )
            logger.info(f"Successfully completed analysis for subtopic_id={subtopic_id}")

        except Exception as e:
            logger.error(f"Background processing failed for subtopic_id={subtopic_id}. Error: {str(e)}", exc_info=True)
            try:
                subtopic_crud.update_status(db, subtopic_id=subtopic_id, status="FAILED")
                logger.info(f"Updated subtopic {subtopic_id} status to FAILED")
            except Exception as update_error:
                logger.error(f"Failed to update subtopic status: {str(update_error)}")

analysis_service = AnalysisService()