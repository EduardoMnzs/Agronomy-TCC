import fitz  # PyMuPDF
from typing import List, Dict
from langchain_core.documents import Document

class PDFProcessor:
    def __init__(self, file_path: str, default_metadata: Dict = None):
        self.file_path = file_path
        self.default_metadata = default_metadata or {}

    def extract_documents(self) -> List[Document]:
        documents = []
        try:
            doc = fitz.open(self.file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Regra estipulada: Documentos escaneados terão fallback p/ EasyOCR depois. 
                if len(text.strip()) < 50:
                    text += "\n[Aviso: Texto escasso extraído. OCR poderá ser engatilhado na pipeline estendida]"
                
                metadata = self.default_metadata.copy()
                metadata["page"] = page_num + 1
                metadata["source"] = self.file_path
                
                documents.append(Document(page_content=text, metadata=metadata))
            doc.close()
        except Exception as e:
            print(f"Erro ao processar PDF {self.file_path}: {str(e)}")
            
        return documents
