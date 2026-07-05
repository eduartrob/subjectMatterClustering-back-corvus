# pyrefly: ignore [missing-import]
import chromadb
from sentence_transformers import SentenceTransformer
import uuid
import os
import logging
import time

# Configuración de MLOps Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VectorStore-MLOps")

class VectorStoreService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self.client.get_or_create_collection(name="classroom_materials")
        logger.info("ChromaDB y SentenceTransformer inicializados correctamente.")

    def store_chunks(self, chunks: list[str], course_id: str, teacher_id: str, file_url: str):
        """Vectoriza los fragmentos y los guarda en ChromaDB con metadatos."""
        if not chunks:
            return

        start_time = time.time()
        embeddings = self.encoder.encode(chunks).tolist()
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        metadatas = [
            {
                "course_id": course_id,
                "teacher_id": teacher_id,
                "file_url": file_url
            } for _ in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Ingestión MLOps: Se vectorizaron e insertaron {len(chunks)} chunks para course_id={course_id} en {elapsed_time:.2f} segundos.")

    def search_similar(self, query: str, course_id: str = None, n_results: int = 3):
        """Busca chunks similares. Si course_id es None, busca en todas las materias."""
        start_time = time.time()
        query_embedding = self.encoder.encode([query]).tolist()
        
        kwargs = {
            "query_embeddings": query_embedding,
            "n_results": n_results
        }
        if course_id:
            kwargs["where"] = {"course_id": course_id}
            
        results = self.collection.query(**kwargs)
        
        # Extraemos el primer grupo de resultados
        retrieved_chunks = results["documents"][0] if results["documents"] else []
        retrieved_metadatas = results["metadatas"][0] if results["metadatas"] else []
        
        elapsed_time = time.time() - start_time
        logger.info(f"Búsqueda MLOps: Query '{query}' recuperó {len(retrieved_chunks)} chunks relevantes en {elapsed_time:.2f} segundos. Course_id={course_id}")
        
        return retrieved_chunks, retrieved_metadatas
