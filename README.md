# 🦅 Corvus AI Microservice — Búsqueda Semántica y RAG

Microservicio backend construido con **FastAPI** y **Python** que provee búsqueda semántica y generación de respuestas con arquitectura RAG (_Retrieval-Augmented Generation_) para la plataforma educativa **Corvus**.

Permite a los estudiantes consultar los materiales de sus materias en lenguaje natural y recibir resúmenes contextualizados, sin que el microservicio almacene físicamente ningún archivo.

---

## ✨ Características principales

- 🔍 **Búsqueda semántica** sobre apuntes y documentos del profesor
- 🤖 **RAG simulado** — arquitectura lista para conectar un LLM local (Llama-3 / Phi-3)
- 🔒 **Aislamiento por materia** — un estudiante solo puede consultar el contenido de su propio curso (`course_id`)
- 💾 **Zero-Storage físico** — los documentos se procesan en RAM y se guardan únicamente como vectores en ChromaDB
- ⚡ **API REST con FastAPI** — documentación automática en `/docs`

---

## 🗂️ Estructura del proyecto

```
subjectMatterClustering-back-corvus/
├── main.py                  # Punto de entrada — instancia FastAPI y registra rutas
├── requirements.txt         # Dependencias del proyecto
├── test_rag.py              # Script de pruebas de integración (ingest + search)
│
├── api/
│   └── routes.py            # Endpoints: /ingest y /search
│
├── models/
│   └── schemas.py           # Modelos Pydantic de request/response
│
└── services/
    ├── nlp_service.py       # Limpieza de texto, chunking y generación de resumen (RAG)
    └── vector_store.py      # Gestión de ChromaDB: almacenamiento y búsqueda de vectores
```

---

## 🚀 Instalación y ejecución

### 1. Requisitos previos

- Python **3.10+**
- `pip`

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Descargar el modelo de lenguaje de spaCy

```bash
python -m spacy download es_core_news_sm
```

### 4. Levantar el servidor

```bash
python main.py
```

El servidor estará disponible en: **`http://localhost:8000`**

La documentación interactiva de la API estará en: **`http://localhost:8000/docs`**

---

## 📡 Endpoints

### `POST /api/v1/ingest`
Recibe el texto extraído de un documento y lo indexa en ChromaDB como vectores.

**Body (JSON):**
```json
{
  "course_id": "2026.9A.C2.MATERIA",
  "teacher_id": "profesor_ejemplo",
  "file_url": "https://drive.google.com/file/d/ejemplo/view",
  "extracted_text": "El clustering es una tarea de aprendizaje no supervisado..."
}
```

**Respuesta:**
```json
{
  "status": "success",
  "message": "Ingested 3 chunks"
}
```

---

### `POST /api/v1/search`
Realiza una búsqueda semántica dentro de una materia y devuelve un resumen generado por RAG junto con los enlaces al material del profesor.

**Body (JSON):**
```json
{
  "query": "¿Cómo funciona el algoritmo K-Means?",
  "course_id": "2026.9A.C2.MATERIA"
}
```

**Respuesta:**
```json
{
  "summary": "La Minería de Datos es una disciplina que...",
  "links": [
    "https://drive.google.com/file/d/ejemplo/view"
  ]
}
```

---

### `GET /`
Verifica que el servicio esté en línea.

```json
{ "status": "online", "message": "Corvus AI Microservice is running" }
```

---

## 🧪 Ejecutar pruebas

Con el servidor corriendo, ejecuta el script de integración:

```bash
python test_rag.py
```

Este script simula:
1. La ingesta de material de dos materias distintas (Programación Móvil y Minería de Datos)
2. Una búsqueda semántica como estudiante, verificando el aislamiento por materia

---

## 🛠️ Stack tecnológico

| Tecnología | Rol |
|---|---|
| **FastAPI** | Framework web y API REST |
| **ChromaDB** | Base de datos vectorial local y persistente |
| **Sentence Transformers** (`all-MiniLM-L6-v2`) | Generación de embeddings |
| **spaCy** (`es_core_news_sm`) | Procesamiento de lenguaje natural en español |
| **NLTK** | Tokenización de texto |
| **Pydantic** | Validación de datos y schemas |
| **Uvicorn** | Servidor ASGI |

---

## 🔮 Trabajo futuro

- [ ] Integrar un LLM local real (Llama-3 o Phi-3) para reemplazar el resumen simulado
- [ ] Soporte para ingesta directa de PDFs en base64 con PyPDF2
- [ ] Autenticación con JWT para validar `teacher_id` y `course_id`
- [ ] Dockerización del servicio

---

## 👥 Proyecto

Desarrollado como microservicio de IA para **Corvus** — plataforma educativa universitaria.
