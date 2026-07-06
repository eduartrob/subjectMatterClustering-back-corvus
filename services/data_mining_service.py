import sqlite3
import re
from collections import Counter
from datetime import datetime, timedelta
import threading

class DataMiningService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataMiningService, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _init_db(self):
        self.db_path = "search_logs.db"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
        self.stopwords = {"de", "la", "que", "el", "en", "y", "a", "los", "del", "se", 
                          "las", "por", "un", "para", "con", "no", "una", "su", "al", 
                          "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este", 
                          "sí", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre",
                          "dime", "explicame", "que", "cual", "cuales", "como"}

    def log_query(self, query: str):
        """Guarda la búsqueda en la base de datos de manera asíncrona (fuego y olvido)."""
        def save():
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO search_queries (query) VALUES (?)", (query.strip(),))
                    conn.commit()
            except Exception as e:
                print(f"Error logging query: {e}")
                
        threading.Thread(target=save, daemon=True).start()

    def _clean_text(self, text: str) -> list:
        # Convertir a minúsculas y quitar signos de puntuación
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        return [w for w in words if w not in self.stopwords and len(w) > 3]

    def get_search_trends(self, limit: int = 4, days: int = 7) -> list:
        """Aplica TF (Term Frequency) simple para obtener las palabras clave más buscadas."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT query FROM search_queries WHERE timestamp >= ?", (date_limit,))
                rows = cursor.fetchall()

            if not rows:
                return ["Inteligencia artificial", "Redes neuronales", "Algoritmos genéticos", "Minería de datos"]

            all_words = []
            full_queries = []
            
            for (query,) in rows:
                full_queries.append(query)
                all_words.extend(self._clean_text(query))
                
            # Primero, buscar n-gramas comunes o palabras clave fuertes
            word_counts = Counter(all_words)
            top_words = [word for word, count in word_counts.most_common(limit * 2)]
            
            # Ahora seleccionamos las queries reales que contengan estas palabras top para que sea legible
            trends = []
            for word in top_words:
                for q in full_queries:
                    if word in q.lower() and q not in trends and len(q) < 40:
                        trends.append(q)
                        break
                if len(trends) >= limit:
                    break
                    
            # Fallback si no hay suficientes
            while len(trends) < limit:
                trends.append("Inteligencia artificial")
                
            return trends[:limit]
            
        except Exception as e:
            print(f"Error calculating trends: {e}")
            return ["Sistemas expertos", "Algoritmos", "Big Data", "Machine Learning"]
