import requests
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"

# ── Colores para la terminal ──────────────────────────────────────────────────
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ── Material de ejemplo que se carga al inicio ────────────────────────────────

MATERIALES = [
    {
        "course_id": "MATERIA_MINERIA",
        "teacher_id": "profesor_a",
        "file_url": "https://drive.google.com/file/d/mineria_apuntes/view",
        "extracted_text": (
            "La minería de datos es una disciplina que extrae patrones y conocimiento "
            "útil de grandes volúmenes de información. El clustering agrupa elementos "
            "según su similitud mediante algoritmos como K-Means y DBSCAN. "
            "K-Means divide los datos en K grupos minimizando la distancia intra-cluster. "
            "DBSCAN detecta grupos de forma arbitraria e identifica valores atípicos (outliers). "
            "Antes de aplicar cualquier algoritmo es fundamental limpiar los datos: "
            "eliminar duplicados, tratar valores nulos y normalizar variables numéricas."
        ),
    },
    {
        "course_id": "MATERIA_MOVIL",
        "teacher_id": "profesor_b",
        "file_url": "https://drive.google.com/file/d/movil_apuntes/view",
        "extracted_text": (
            "Flutter es un framework de Google para crear aplicaciones móviles nativas "
            "para Android e iOS desde una sola base de código. "
            "Clean Architecture separa la app en capas: presentación, dominio e infraestructura, "
            "haciendo el código mantenible y testeable. "
            "Provider es el gestor de estado recomendado para Flutter: permite compartir datos "
            "entre pantallas sin pasar parámetros manualmente. "
            "Un UseCase encapsula una regla de negocio específica y es invocado desde el ViewModel."
        ),
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def wrap(text: str, width: int = 70, indent: str = "   ") -> str:
    """Ajusta el texto a un ancho máximo con sangría."""
    words = text.split()
    lines, line = [], indent
    for word in words:
        if len(line) + len(word) + 1 > width:
            lines.append(line)
            line = indent + word + " "
        else:
            line += word + " "
    if line.strip():
        lines.append(line)
    return "\n".join(lines)

def verificar_servidor() -> bool:
    """Reintenta hasta 5 veces con 1s de espera (uvicorn reload tarda un momento)."""
    for intento in range(5):
        try:
            r = requests.get("http://localhost:8000/", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        if intento < 4:
            time.sleep(1)
    return False

def cargar_material(material: dict) -> bool:
    try:
        r = requests.post(f"{BASE_URL}/ingest", json=material, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def buscar(query: str) -> dict | None:
    try:
        r = requests.post(f"{BASE_URL}/search-smart", json={"query": query}, timeout=10)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return {"error": r.json().get("detail", "Materia no detectada")}
        return {"error": f"Error {r.status_code}: {r.text}"}
    except Exception as e:
        return {"error": str(e)}

# ── Flujo principal ───────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{CYAN}{'━' * 54}{RESET}")
    print(f"{BOLD}{CYAN}   🦅 Corvus AI — Simulador de Buscador Móvil{RESET}")
    print(f"{BOLD}{CYAN}{'━' * 54}{RESET}\n")

    # 1. Verificar servidor
    print(f"  Verificando servidor...", end=" ", flush=True)
    if not verificar_servidor():
        print(f"\n{RED}❌ El servidor no está corriendo.{RESET}")
        print(f"   Ejecuta en otra terminal: {BOLD}venv/bin/python main.py{RESET}\n")
        sys.exit(1)
    print(f"{GREEN}✅ En línea{RESET}\n")

    # 2. Cargar material de ejemplo (solo si no existe ya)
    print(f"  {DIM}Cargando material de ejemplo...{RESET}", end=" ", flush=True)
    resultados = [cargar_material(m) for m in MATERIALES]
    print(f"{GREEN}✅ Listo{RESET}\n")

    # 3. Instrucciones
    print(f"  {BOLD}Escribe tu búsqueda como lo harías en la app.{RESET}")
    print(f"  {DIM}Ejemplos: 'mineria', 'quiero saber sobre flutter', 'clustering'{RESET}")
    print(f"  {DIM}Escribe 'salir' para terminar.{RESET}\n")
    print(f"  {'─' * 50}\n")

    # 4. Bucle de búsqueda
    while True:
        try:
            query = input(f"  {BOLD}{YELLOW}🔍 Buscar:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() == "salir":
            break

        resultado = buscar(query)

        if resultado is None or "error" in resultado:
            msg = resultado.get("error", "Error desconocido") if resultado else "Sin respuesta"
            print(f"\n  {RED}⚠️  {msg}{RESET}\n")
        else:
            materia = resultado.get("detected_subject", "—")
            resumen = resultado.get("summary", "")
            links   = resultado.get("links", [])

            print(f"\n  {DIM}Materia detectada:{RESET} {BOLD}{CYAN}{materia}{RESET}")
            print(f"\n  {BOLD}{GREEN}📝 Respuesta:{RESET}")
            print(wrap(resumen))

            if links:
                print(f"\n  {BOLD}🔗 Material del profesor:{RESET}")
                for link in links:
                    print(f"     → {link}")

        print(f"\n  {'─' * 50}\n")

    print(f"\n  {BOLD}👋 ¡Hasta luego!{RESET}\n")


if __name__ == "__main__":
    main()
