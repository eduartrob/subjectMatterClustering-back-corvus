# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from fastembed import TextEmbedding
import uuid
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VectorStore-MLOps")

class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(path="./qdrant_data")
        self.encoder = TextEmbedding(model_name="paraphrase-multilingual-MiniLM-L12-v2")
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
