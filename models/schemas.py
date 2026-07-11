from pydantic import BaseModel
from typing import List, Optional

class IngestRequest(BaseModel):
    course_id: str
    course_name: str
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
    query: str

class SmartSearchResponse(BaseModel):
    detected_subject: str
    summary: str
    links: List[str]
