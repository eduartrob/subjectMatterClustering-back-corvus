import os
import uuid
import numpy as np
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from fastembed import TextEmbedding
import logging

logger = logging.getLogger('VectorStore-MLOps')
logging.basicConfig(level=logging.INFO)

class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(path="./qdrant_data")
        self.encoder = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.collection_name = "classroom_materials"

        self._init_collection()
        self._init_theme_classifier()

    def _init_collection(self):
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info(f"Coleccion '{self.collection_name}' creada en Qdrant.")
        logger.info("Qdrant y FastEmbed inicializados correctamente.")

    def _init_theme_classifier(self):
        self.themes = [
            {"label": "Tecnologia y Software", "color": "0xFF1E88E5", "icon": "smartphone_rounded"},
            {"label": "Matematicas y Logica", "color": "0xFFE53935", "icon": "calculate_rounded"},
            {"label": "Ciencias Naturales", "color": "0xFF43A047", "icon": "science_rounded"},
            {"label": "Humanidades", "color": "0xFF8E24AA", "icon": "menu_book_rounded"},
            {"label": "Diseno y Arte", "color": "0xFFF4511E", "icon": "palette_rounded"},
            {"label": "Negocios", "color": "0xFFFFB300", "icon": "business_center_rounded"}
        ]
        self.theme_embeddings = list(self.encoder.embed([t["label"] for t in self.themes]))

    def store_chunks(self, chunks, course_id: str, course_name: str, teacher_id: str, file_url: str):
        if not chunks:
            return
        points = []
        embeddings = list(self.encoder.embed(chunks))

        for i, chunk in enumerate(chunks):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embeddings[i].tolist(),
                    payload={
                        "text": chunk,
                        "course_id": course_id,
                        "course_name": course_name,
                        "teacher_id": teacher_id,
                        "file_url": file_url
                    }
                )
            )

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def search_similar(self, query: str, course_id: str = None, n_results: int = 4):
        import time
        start_time = time.time()

        query_vector = list(self.encoder.embed([query]))[0].tolist()

        must_conditions = []
        if course_id:
            must_conditions.append(
                FieldCondition(
                    key="course_id",
                    match=MatchValue(value=course_id)
                )
            )

        search_filter = Filter(must=must_conditions) if must_conditions else None

        # qdrant-client >= 1.7 uses query_points instead of search
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=n_results,
            score_threshold=0.35
        )

        latency = time.time() - start_time
        # results.points is the list in qdrant-client 1.7+
        points = results.points
        logger.info(f"Busqueda MLOps: Query '{query}' recupero {len(points)} chunks en {latency:.2f}s. Course_id={course_id}")

        chunks = [p.payload.get("text", "") for p in points]
        metadatas = [p.payload for p in points]
        return chunks, metadatas

    def infer_course_theme(self, course_name: str) -> dict:
        try:
            course_emb = list(self.encoder.embed([course_name]))[0]

            def cosine_similarity(v1, v2):
                return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

            best_score = -1
            best_theme = self.themes[0]

            for i, theme_emb in enumerate(self.theme_embeddings):
                score = cosine_similarity(course_emb, theme_emb)
                if score > best_score:
                    best_score = score
                    best_theme = self.themes[i]

            return best_theme
        except Exception as e:
            logger.error(f"Error infering theme for {course_name}: {e}")
            return self.themes[0]

    def get_available_courses(self):
        try:
            records, next_page = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=["course_id", "course_name"],
                with_vectors=False
            )

            courses_map = {}
            for record in records:
                if "course_id" in record.payload:
                    c_id = record.payload["course_id"]
                    c_name = record.payload.get("course_name", str(c_id))
                    courses_map[c_id] = c_name

            while next_page is not None:
                records, next_page = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,
                    offset=next_page,
                    with_payload=["course_id", "course_name"],
                    with_vectors=False
                )
                for record in records:
                    if "course_id" in record.payload:
                        c_id = record.payload["course_id"]
                        c_name = record.payload.get("course_name", str(c_id))
                        courses_map[c_id] = c_name

            enriched_courses = []
            for c_id, c_name in courses_map.items():
                theme = self.infer_course_theme(c_name)
                enriched_courses.append({
                    "id": c_id,
                    "name": c_name,
                    "color": theme["color"],
                    "icon": theme["icon"]
                })
            return enriched_courses
        except Exception as e:
            logger.error(f"Error getting available courses: {e}")
            return []
