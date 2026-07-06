import requests

BASE_URL = "http://localhost:8000/api/v1"

def main():
    print("==================================================")
    print("   🦅 PRUEBA DE INTEGRACIÓN CON GOOGLE DRIVE")
    print("==================================================")
    
    # 1. Pedir datos
    access_token = input("\n🔑 Pega tu Access Token de Google: ").strip()
    folder_id = input("📁 Pega el ID de la carpeta de Drive: ").strip()
    
    if not access_token or not folder_id:
        print("❌ Error: Necesitas ingresar un token y un ID de carpeta.")
        return
        
    payload = {
        "course_id": "MATERIA_REAL_01",
        "teacher_id": "profe_demo",
        "folder_id": folder_id,
        "access_token": access_token
    }
    
    print("\n⏳ Conectando con Google Drive y extrayendo PDFs...")
    print("   (Esto puede tardar unos segundos dependiendo del tamaño del PDF)")
    
    try:
        r = requests.post(f"{BASE_URL}/ingest", json=payload, timeout=60)
        
        if r.status_code == 200:
            print("\n✅ ¡ÉXITO! Los PDFs fueron procesados en memoria.")
            print(f"   Respuesta del servidor: {r.json()}")
            print("\n👉 Siguiente paso: Corre 'venv/bin/python test_interactivo.py'")
            print("   y hazle una pregunta sobre el PDF que acabas de subir.")
        else:
            print(f"\n❌ Error del servidor (Código {r.status_code}):")
            print(r.text)
            if r.status_code == 401 or "invalid" in r.text.lower():
                print("\n💡 Tip: Tu Access Token probablemente expiró o es incorrecto.")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: El servidor FastAPI no está corriendo.")
        print("   Ejecuta 'venv/bin/python main.py' en otra terminal.")

if __name__ == "__main__":
    main()
