import io
from typing import List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import PyPDF2

class DriveService:
    def __init__(self, access_token: str):
        creds = Credentials(token=access_token)
        self.service = build('drive', 'v3', credentials=creds)

    def get_files_in_folder(self, folder_id: str) -> List[dict]:
        """Obtiene la lista de archivos PDF dentro de una carpeta específica."""
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        
        results = self.service.files().list(
            q=query,
            pageSize=10,
            fields="nextPageToken, files(id, name, webViewLink)"
        ).execute()
        
        return results.get('files', [])

    def download_and_extract_pdf(self, file_id: str) -> str:
        """Descarga el PDF en memoria RAM y extrae su texto usando PyPDF2."""
        request = self.service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        file_stream.seek(0)
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
        resultados = []
        
        for archivo in archivos:
            texto = self.download_and_extract_pdf(archivo['id'])
            if texto:
                resultados.append({
                    "file_url": archivo.get('webViewLink', f"https://drive.google.com/file/d/{archivo['id']}/view"),
                    "extracted_text": texto
                })
                
        return resultados
