import google.genai as genai
from google.genai.types import Part
from app.core.config import settings
from typing import List, Dict, Any, Optional
import json
import os
import pathlib
import logging
import re

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    GOOGLE_API_KEY = os.environ["GEMINI_API_KEY"]
    MODEL_ID = "gemini-2.5-flash"
    if not GOOGLE_API_KEY:
        raise ValueError("La variable de entorno GOOGLE_API_KEY no está configurada.")
    
    gemini_client_instance = genai.Client(api_key=GOOGLE_API_KEY)
    logger.info("Gemini client initialized successfully")
except ValueError as e:
    INITIALIZATION_ERROR_MESSAGE = f"Error de configuración de Gemini: {e}"
    logger.error(INITIALIZATION_ERROR_MESSAGE)
except Exception as e_global_init:
    INITIALIZATION_ERROR_MESSAGE = f"Error inesperado durante la inicialización global de Gemini: {e_global_init}"
    logger.error(INITIALIZATION_ERROR_MESSAGE)

def extract_json_from_response(response_text: str) -> str:
    """
    Extrae el JSON del texto de respuesta, manejando casos donde el JSON puede estar
    dentro de un bloque de código markdown o directamente como texto.
    """
    # Patrón para encontrar JSON dentro de bloques de código markdown
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    
    # Buscar si hay un bloque de código
    match = re.search(code_block_pattern, response_text)
    
    if match:
        logger.info("JSON encontrado dentro de un bloque de código markdown")
        # Extraer solo el contenido dentro del bloque de código
        return match.group(1).strip()
    else:
        logger.info("No se encontró bloque de código markdown, usando el texto completo")
        return response_text.strip()

async def analyze_pdf_for_study(pdf_content: bytes) -> Dict[str, Any]:
    """
    Analiza el contenido de un PDF (proporcionado como bytes) y genera una guía de 
    estudio estructurada en formato JSON usando Gemini.
    """
    
    logger.info(f"Using model: {MODEL_ID}")
    
    if not pdf_content:
        logger.error("PDF content is empty")
        raise ValueError("PDF content cannot be empty")
        
    logger.info(f"PDF content size: {len(pdf_content)} bytes")
    
    try:
        pdf_file_part = Part.from_bytes(
            data=pdf_content,
            mime_type='application/pdf',
        )
        logger.info("Successfully created PDF part for Gemini")
    except Exception as e:
        logger.error(f"Error creating PDF part: {str(e)}")
        raise

    prompt = """
    Eres un asistente educativo experto. Tu tarea es analizar el documento PDF adjunto y descomponerlo en una guía de estudio estructurada en formato JSON.

    Basado en el contenido del documento, debes realizar las siguientes acciones:
    1.  **Identificar Conceptos Clave**: Extrae una lista de los 5 a 10 conceptos o términos más importantes del texto.
    2.  **Desglosar en Subtemas**: Divide el contenido principal en 3 a 5 subtemas lógicos. Cada subtema debe tener un título claro.
    3.  **Generar Flashcards por Subtema**: Para cada subtema, crea entre 3 y 5 flashcards. Cada flashcard debe tener un 'front' (pregunta o término) y un 'back' (respuesta o definición).
    4.  **Generar un Quiz por Subtema**: Para cada subtema, crea un pequeño quiz de 3 a 5 preguntas de opción múltiple. Cada pregunta debe tener:
        - 'question_text': El texto de la pregunta.
        - 'options': Una lista de 4 strings con las posibles respuestas.
        - 'correct_answer_index': El índice (0 a 3) de la respuesta correcta en la lista de opciones.
        - 'explanation': Una breve explicación de por qué la respuesta es correcta.
    5.  **Asignar Dificultad al Quiz**: Asigna una dificultad general al quiz ('Fácil', 'Medio', 'Difícil').

    La estructura de salida DEBE ser ESTRICTAMENTE un UNICO objeto JSON con el siguiente formato EXACTO:
    {
      "key_concepts": ["Concepto 1", "Concepto 2", ...],
      "subtopics": [
        {
          "title": "Título del Subtema 1",
          "flashcards": [
            {"front": "Pregunta A", "back": "Respuesta A"}
          ],
          "quizzes": [
            {
              "title": "Quiz sobre Título del Subtema 1",
              "description": "Una descripción sobre el quizz", 
              "difficulty": "Medio",
              "questions": [
                {
                  "question_text": "¿Cuál es la pregunta?",
                  "options": ["Opción 1", "Opción Correcta", "Opción 3", "Opción 4"],
                  "correct_answer_index": 1,
                  "explanation": "La respuesta es correcta porque..."
                }
              ]
            }
          ]
        }
      ]
    }
    
    Ahora, analiza el documento y genera la estructura JSON completa.
    """

    try:
        # Enviamos el prompt y el archivo PDF en la misma petición
        logger.info("Sending request to Gemini API...")
        response = await gemini_client_instance.aio.models.generate_content(
            model=MODEL_ID,
            contents=[pdf_file_part, prompt]
        )
        
        if not response or not response.text:
            logger.error("Empty response from Gemini API")
            raise ValueError("Empty response from Gemini API")
            
        logger.info("Successfully received response from Gemini")
        logger.info(f"{response.text}")
        logger.debug(f"Raw response text length: {len(response.text)}")
        
        # Extraer el JSON de la respuesta
        json_text = extract_json_from_response(response.text)
        logger.debug(f"Extracted JSON text length: {len(json_text)}")
        
        try:
            parsed_response = json.loads(json_text)
            logger.info("Successfully parsed JSON response")
            return parsed_response
        except json.JSONDecodeError as json_error:
            logger.error(f"Failed to parse Gemini response as JSON: {str(json_error)}")
            logger.debug(f"JSON text that failed to parse: {json_text[:500]}...")  # Log first 500 chars
            raise
            
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        raise ValueError(f"Could not get a valid structured response from Gemini. Error: {e}")