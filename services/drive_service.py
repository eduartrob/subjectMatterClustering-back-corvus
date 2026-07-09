import io
from typing import List
import requests
import PyPDF2

class DriveService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }

    def get_files_in_folder(self, folder_id: str) -> List[dict]:
        """Obtiene la lista de archivos PDF dentro de una carpeta específica usando requests."""
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        url = "https://www.googleapis.com/drive/v3/files"
        params = {
            'q': query,
            'pageSize': 10,
            'fields': "nextPageToken, files(id, name, webViewLink)"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching files: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        return data.get('files', [])

    def download_and_extract_pdf(self, file_id: str) -> str:
        """Descarga el PDF en memoria RAM y extrae su texto usando PyPDF2 y requests."""
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Error downloading file {file_id}: {response.status_code} - {response.text}")
            return ""
            
        file_stream = io.BytesIO(response.content)
        texto_extraido = ""
        
        try:
            lector_pdf = PyPDF2.PdfReader(file_stream)
            for pagina in lector_pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_extraido += texto + "\n"
        except Exception as e:
            print(f"Error extrayendo texto del PDF {file_id}: {e}")
            
        return texto_extraido.strip()

    def process_folder(self, folder_id: str) -> List[dict]:
        """
        Lee todos los PDFs de una carpeta, extrae el texto y devuelve
        una lista de diccionarios listos para ser guardados en ChromaDB.
        """
        archivos = self.get_files_in_folder(folder_id)
        print(f"Archivos encontrados: {len(archivos)}")
        resultados = []
        
        for archivo in archivos:
            texto = self.download_and_extract_pdf(archivo['id'])
            if texto:
                resultados.append({
                    "file_url": archivo.get('webViewLink', f"https://drive.google.com/file/d/{archivo['id']}/view"),
                    "extracted_text": texto
                })
                
        return resultados
