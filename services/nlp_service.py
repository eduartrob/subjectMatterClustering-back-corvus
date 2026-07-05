import nltk
import spacy
from typing import List
import os
from dotenv import load_dotenv
from groq import Groq

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
        load_dotenv()
        self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

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
        
        prompt = f"""
Eres un asistente académico experto de la aplicación Corvus. Tu objetivo es responder la duda del estudiante utilizando ÚNICAMENTE la siguiente información extraída de los materiales del profesor. 
No inventes información, si la respuesta no está en el contexto, di que no hay suficiente información en los materiales.
Responde de manera amable, clara y estructurada.

Consulta del estudiante: {query}

Contexto (Material del profesor):
{context}
"""
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente académico útil y preciso."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.3,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            resumen_simulado = context[:500].strip()
            if len(context) > 500:
                resumen_simulado += "..."
            return f"Hubo un error contactando a la IA, pero aquí está el extracto más relevante:\n\n❝ {resumen_simulado} ❞\n\n(Error: {str(e)})"
