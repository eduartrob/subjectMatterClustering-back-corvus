from pydantic import BaseModel
from typing import List

class IngestRequest(BaseModel):
    course_id: str
    teacher_id: str
    folder_id: str
    access_token: str

class SearchRequest(BaseModel):
    query: str
    course_id: str

class SearchResponse(BaseModel):
    summary: str
    links: List[str]

class SmartSearchRequest(BaseModel):
    """Recibe solo la query; el backend detecta la materia automáticamente."""
    query: str

class SmartSearchResponse(BaseModel):
    detected_subject: str   # Nombre legible de la materia detectada
    summary: str
    links: List[str]
