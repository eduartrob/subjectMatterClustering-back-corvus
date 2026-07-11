from fastapi import APIRouter, HTTPException
from models.schemas import (
    IngestRequest, SearchRequest, SearchResponse,
    SmartSearchRequest, SmartSearchResponse
)
from services.nlp_service import NLPService
from services.vector_store import VectorStoreService
from services.drive_service import DriveService
from services.data_mining_service import DataMiningService

router = APIRouter()
nlp_service = NLPService()
vector_store = VectorStoreService()
data_mining = DataMiningService()

@router.post("/ingest")
async def ingest_material(request: IngestRequest):
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
                course_name=request.course_name,
                teacher_id=request.teacher_id,
                file_url=mat["file_url"]
            )
            total_chunks += len(chunks)

        return {"status": "success", "message": f"Ingested {len(materiales)} files ({total_chunks} chunks)"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
async def search_materials(request: SearchRequest):
    try:
        data_mining.log_query(request.query)

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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-smart", response_model=SmartSearchResponse)
async def search_smart(request: SmartSearchRequest):
    try:
        data_mining.log_query(request.query)

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

        detected_course_id = metadatas_top[0].get("course_id", "Desconocida")
        detected_course_name = metadatas_top[0].get("course_name", detected_course_id)

        chunks, metadatas = vector_store.search_similar(
            query=request.query,
            course_id=detected_course_id,
            n_results=3
        )

        summary = nlp_service.generate_summary(request.query, chunks)
        links = list(set([meta.get("file_url") for meta in metadatas if "file_url" in meta]))

        return SmartSearchResponse(
            detected_subject=detected_course_name,
            summary=summary,
            links=links
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-courses")
async def get_available_courses():
    try:
        courses = vector_store.get_available_courses()
        return {"courses": courses}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-trends")
async def get_search_trends(limit: int = 4):
    try:
        trends = data_mining.get_search_trends(limit=limit)
        return {"trends": trends}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
