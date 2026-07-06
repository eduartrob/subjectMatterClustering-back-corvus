from fastapi import APIRouter, HTTPException
from models.schemas import (
    IngestRequest, SearchRequest, SearchResponse,
    SmartSearchRequest, SmartSearchResponse
)
from services.nlp_service import NLPService
from services.vector_store import VectorStoreService
from services.drive_service import DriveService

router = APIRouter()
nlp_service = NLPService()
vector_store = VectorStoreService()

@router.post("/ingest")
async def ingest_material(request: IngestRequest):
    """
    Se conecta a Google Drive con el token proporcionado, lee todos los PDFs de la
    carpeta de la materia, extrae el texto en memoria y lo indexa en ChromaDB como vectores.
    Garantiza Zero-Storage físico: se procesa en RAM sin guardar archivos.
    """
    try:
        drive_service = DriveService(request.access_token)
        materiales = drive_service.process_folder(request.folder_id)
        
        if not materiales:
            return {"status": "success", "message": "No se encontraron PDFs o estaban vacíos en esta carpeta."}
            
        total_chunks = 0
        for mat in materiales:
            chunks = nlp_service.chunk_text(mat["extracted_text"])
            vector_store.store_chunks(
                chunks=chunks,
                course_id=request.course_id,
                teacher_id=request.teacher_id,
                file_url=mat["file_url"]
            )
            total_chunks += len(chunks)
            
        return {"status": "success", "message": f"Ingested {len(materiales)} files ({total_chunks} chunks)"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
async def search_materials(request: SearchRequest):
    """
    Búsqueda semántica con RAG: recupera chunks relevantes de ChromaDB
    y genera un resumen contextualizado por materia.
    """
    try:
        chunks, metadatas = vector_store.search_similar(
            query=request.query,
            course_id=request.course_id
        )
        summary = nlp_service.generate_summary(request.query, chunks)
        links = list(set([meta.get("file_url") for meta in metadatas if "file_url" in meta]))
        
        return SearchResponse(
            summary=summary,
            links=links
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-smart", response_model=SmartSearchResponse)
async def search_smart(request: SmartSearchRequest):
    """
    Buscador principal para la app móvil.
    Busca la query en toda la base de datos (ChromaDB), detectando automáticamente
    a qué materia pertenece el material más relevante y generando el resumen.
    """
    try:
        # 1. Detección de la materia más relevante
        _, metadatas_top = vector_store.search_similar(
            query=request.query,
            course_id=None,
            n_results=1
        )
        
        if not metadatas_top:
            raise HTTPException(
                status_code=404,
                detail="No encontré ningún material relacionado a tu búsqueda en ninguna clase."
            )
            
        detected_course = metadatas_top[0].get("course_id", "Desconocida")
        
        # 2. Búsqueda estricta en la materia detectada
        chunks, metadatas = vector_store.search_similar(
            query=request.query,
            course_id=detected_course,
            n_results=3
        )
        
        summary = nlp_service.generate_summary(request.query, chunks)
        links = list(set([meta.get("file_url") for meta in metadatas if "file_url" in meta]))

        return SmartSearchResponse(
            detected_subject=detected_course,
            summary=summary,
            links=links
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
