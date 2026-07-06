import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def print_separator(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def test_ingest():
    print_separator("PRUEBA DE INGESTA (ETL)")
    
    payload_moviles = {
        "course_id": "2026.C2_9A",
        "teacher_id": "ali_lopez",
        "file_url": "https://drive.google.com/file/d/pdf_provider_architecture/view",
        "extracted_text": "En Flutter, Provider es un gestor de estado recomendado. Combinado con Clean Architecture, permite separar la capa de presentación de la lógica de negocio, haciendo que las aplicaciones sean mantenibles y escalables. Un UseCase se encarga de ejecutar reglas específicas del negocio."
    }
    
    print("Enviando material de Programación para móviles II...")
    response = requests.post(f"{BASE_URL}/ingest", json=payload_moviles)
    print(f"Status Code: {response.status_code}")
    print(f"Respuesta: {response.json()}")

    payload_mineria = {
        "course_id": "2026.9A.C2.MINERIA",
        "teacher_id": "horacio_solis",
        "file_url": "https://drive.google.com/file/d/pdf_clustering/view",
        "extracted_text": "El clustering es una tarea de aprendizaje no supervisado. Agrupa elementos basándose en la distancia y similitud matemática de sus características, como el algoritmo K-Means o DBSCAN."
    }
    
    print("\nEnviando material de Minería de Datos...")
    response2 = requests.post(f"{BASE_URL}/ingest", json=payload_mineria)
    print(f"Status Code: {response2.status_code}")
    print(f"Respuesta: {response2.json()}")


def test_search():
    print_separator("PRUEBA DE BÚSQUEDA Y RAG (SIMULADOR DE ESTUDIANTE)")
    
    payload_busqueda = {
        "query": "¿Cómo funciona Clean Architecture con Provider?",
        "course_id": "2026.C2_9A"
    }
    
    print(f"Buscando: '{payload_busqueda['query']}' en la materia {payload_busqueda['course_id']}...\n")
    
    response = requests.post(f"{BASE_URL}/search", json=payload_busqueda)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n📝 RESUMEN GENERADO POR LA IA LOCAL (RAG):")
        print(f" > {data['summary']}")
        
        print("\n🔗 ENLACES AL DRIVE DEL PROFESOR (SOLO LECTURA):")
        for link in data['links']:
            print(f" > {link}")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("Iniciando Pruebas de Corvus Microservicio IA...")
    try:
        requests.get("http://localhost:8000/")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: El servidor FastAPI no está corriendo. Ejecuta 'python main.py' primero.")
        exit(1)
        
    test_ingest()
    time.sleep(1)  # Espera breve para que ChromaDB finalice la indexación
    test_search()
    
    print_separator("PRUEBAS FINALIZADAS EXITOSAMENTE")
