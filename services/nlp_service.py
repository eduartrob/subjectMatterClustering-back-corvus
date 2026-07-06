import nltk
import spacy
from typing import List
import os
import json
import requests

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    nlp = spacy.blank("es")

class NLPService:
    def __init__(self):
        self.chunk_size = 500
        self.overlap = 50
        self.llm_service_url = os.environ.get("LLM_SERVICE_URL", "http://localhost:3003/api/v1/llm")
        self.config_path = "./chroma_db/app_config.json"

    def _get_llm_provider(self) -> str:
        """Lee el proveedor LLM seleccionado por el administrador desde el config centralizado."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("llm_provider", "groq")
        except Exception:
            pass
        return "groq"

    def clean_text(self, text: str) -> str:
        """Limpia el texto base eliminando saltos de línea excesivos y basura."""
        import re
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def chunk_text(self, text: str) -> List[str]:
        clean = self.clean_text(text)
        chunks = []
        for i in range(0, len(clean), self.chunk_size - self.overlap):
            chunks.append(clean[i:i + self.chunk_size])
        return chunks

    def generate_summary(self, query: str, retrieved_chunks: List[str]) -> str:
        if not retrieved_chunks:
            return "Lo siento, no encontré información sobre este tema en los apuntes de la clase."
        
        context = "\n\n".join(retrieved_chunks)
        
        try:
            response = requests.post(
                f"{self.llm_service_url}/generate-rag-summary",
                json={
                    "query": query,
                    "context": context,
                    "provider": self._get_llm_provider()
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("summary", "No se generó resumen.")
        except Exception as e:
            resumen_simulado = context[:500].strip()
            if len(context) > 500:
                resumen_simulado += "..."
            return f"Hubo un error contactando al microservicio LLM, pero aquí está el extracto más relevante:\n\n❝ {resumen_simulado} ❞\n\n(Error: {str(e)})"
