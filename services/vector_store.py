# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from fastembed import TextEmbedding
import uuid
import os
import logging
import time
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VectorStore-MLOps")

class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(path="./qdrant_data")
        self.encoder = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.collection_name = "classroom_materials"
        
        # Crear la colección si no existe
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info(f"Colección '{self.collection_name}' creada en Qdrant.")
        else:
            logger.info(f"Colección '{self.collection_name}' cargada en Qdrant.")

        # Definir temas base para clasificación semántica
        self.themes = [
            {"label": "Ciencias Exactas", "keywords": "matemáticas, física, cálculo, álgebra, geometría, ecuaciones, estadística, probabilidad", "color": "0xFFE53935", "icon": "calculate_rounded"}, # Rojo
            {"label": "Desarrollo", "keywords": "programación, software, desarrollo, web, móvil, código, arquitectura, algoritmos, aplicaciones", "color": "0xFF1E88E5", "icon": "smartphone_rounded"}, # Azul
            {"label": "Datos e IA", "keywords": "datos, inteligencia artificial, minería, redes neuronales, machine learning, big data", "color": "0xFF8E24AA", "icon": "data_exploration_rounded"}, # Morado
            {"label": "Diseño", "keywords": "diseño, arte, interfaces, UI, UX, usabilidad, gráfico", "color": "0xFFE91E63", "icon": "design_services_rounded"}, # Rosa
            {"label": "Idiomas", "keywords": "inglés, español, literatura, gramática, francés, redacción, idiomas, lenguaje", "color": "0xFF00ACC1", "icon": "language_rounded"}, # Cian
            {"label": "Humanidades", "keywords": "historia, geografía, filosofía, psicología, derecho, leyes, ética", "color": "0xFFFF8F00", "icon": "account_balance_rounded"}, # Naranja
            {"label": "Gerencia", "keywords": "administración, gerencia, negocios, contabilidad, liderazgo, habilidades blandas, economía", "color": "0xFF43A047", "icon": "business_center_rounded"}, # Verde
        ]
        
        # Pre-calcular embeddings de los temas para que sea rápido
        self.theme_embeddings = list(self.encoder.embed([t["keywords"] for t in self.themes]))

        logger.info("Qdrant y FastEmbed inicializados correctamente.")

    def store_chunks(self, chunks: list[str], course_id: str, teacher_id: str, file_url: str):
        """Vectoriza los fragmentos y los guarda en Qdrant con metadatos."""
        if not chunks:
            return

        start_time = time.time()
        
        # Generar embeddings (devuelve un generador, lo convertimos a lista)
        embeddings_gen = self.encoder.embed(chunks)
        embeddings = [list(e) for e in embeddings_gen]
        
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, id_)),
                vector=embeddings[i],
                payload={
                    "course_id": course_id,
                    "teacher_id": teacher_id,
                    "file_url": file_url,
                    "text": chunks[i]
                }
            ) for i, id_ in enumerate(ids)
        ]

        self.client.upsert(collection_name=self.collection_name, points=points)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Ingestión MLOps: Se vectorizaron e insertaron {len(chunks)} chunks para course_id={course_id} en {elapsed_time:.2f} segundos.")

    def search_similar(self, query: str, course_id: str = None, n_results: int = 3):
        """Busca chunks similares. Si course_id es None, busca en todas las materias."""
        start_time = time.time()
        
        # Generar embedding del query
        query_embedding = list(list(self.encoder.embed([query]))[0])
        
        query_filter = None
        if course_id:
            query_filter = Filter(
                must=[FieldCondition(
                    key="course_id",
                    match=MatchValue(value=course_id)
                )]
            )
            
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=n_results,
            query_filter=query_filter,
            with_payload=True
        )
        
        retrieved_chunks = []
        retrieved_metadatas = []
        for hit in results.points:
            retrieved_chunks.append(hit.payload.get("text", ""))
            retrieved_metadatas.append(hit.payload)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Búsqueda MLOps: Query '{query}' recuperó {len(retrieved_chunks)} chunks relevantes en {elapsed_time:.2f} segundos. Course_id={course_id}")
        
        return retrieved_chunks, retrieved_metadatas

    def get_available_courses(self):
        """Devuelve una lista de los course_ids únicos guardados en Qdrant."""
        try:
            records, next_page = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=["course_id"],
                with_vectors=False
            )
            courses = set()
            for record in records:
                if "course_id" in record.payload:
                    courses.add(record.payload["course_id"])
            
            while next_page is not None:
                records, next_page = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,
                    offset=next_page,
                    with_payload=["course_id"],
                    with_vectors=False
                )
                for record in records:
                    if "course_id" in record.payload:
                        courses.add(record.payload["course_id"])
                        
            # Transformar a objetos enriquecidos con IA
            enriched_courses = []
            for c in courses:
                theme = self.infer_course_theme(c)
                enriched_courses.append({
                    "name": c,
                    "color": theme["color"],
                    "icon": theme["icon"]
                })
                
            return enriched_courses
        except Exception as e:
            logger.error(f"Error getting available courses: {e}")
            return []

    def infer_course_theme(self, course_name: str) -> dict:
        """Asigna un tema basado en similitud coseno usando FastEmbed."""
        try:
            course_emb = list(self.encoder.embed([course_name]))[0]
            
            # Función auxiliar para similitud coseno
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
