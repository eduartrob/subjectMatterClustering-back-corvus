from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Corvus IA Microservice",
    description="Microservicio de Clustering, Búsqueda Semántica y RAG para Corvus",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "online", "message": "Corvus AI Microservice is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3005, reload=True)
