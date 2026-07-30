# Subject Matter Clustering Service — Corvus Platform

Este microservicio pertenece a la plataforma **CORVUS**. Es el módulo encargado del **análisis semántico y clasificación de asignaturas, materias académicas y temas bloqueados** en los proyectos integradores.

---

## 🎯 Función en el Ecosistema CORVUS
* **Matriz de Asignaturas:** Evaluación de materias curriculares para sugerencias temáticas de proyectos.
* **Control de Temas Bloqueados:** Validación de restricción de contenidos por carrera y universidad.
* **Integración con Google Drive:** Procesamiento de carpetas y repositorios bibliográficos de referencia.

---

## ⚙️ Tecnologías
* **Lenguaje & Framework:** Python 3.10+, FastAPI, Uvicorn.
* **Integraciones:** Google Drive API v3.
* **Base de Datos:** Acceso a catálogos institucionales.

---

## 🛠️ Ejecución Local Independiente

### 1. Entorno Virtual & Dependencias
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variables de Entorno
Crea un archivo `.env` basado en `.env.example`:
```env
PORT=8003
```

### 3. Iniciar Servidor en Desarrollo
```bash
uvicorn main:app --reload --port 8003
```
Documentación interactiva disponible en `http://localhost:8003/docs`.

---

## 🐳 Ejecución con Docker

```bash
docker build -t corvus-subject-matter-service .
docker run -p 8003:8003 --env-file .env corvus-subject-matter-service
```

---

## 🔗 Integración con la Orquestación de CORVUS
Orquestado mediante **`orchestration-back-corvus`** y enrutado por el API Gateway (`/api/v1/subjects`).
