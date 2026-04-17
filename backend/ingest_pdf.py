import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ingestion.pdf_processor import PDFProcessor
from core.ingestion.chunker import split_documents
from infrastructure.vectordb.qdrant_adapter import QdrantAdapter

def main():
    if len(sys.argv) < 2:
        print("Uso:   python ingest_pdf.py <caminho_do_pdf>")
        print("Exemplo: python ingest_pdf.py manual_soja.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Erro: O arquivo '{pdf_path}' não foi encontrado!")
        sys.exit(1)

    # Passo 1: Extração do Texto Bruto pagína por página com PyMuPDF
    print(f"\n[1/3] Lendo e extraindo texto do PDF: {pdf_path}...")
    processor = PDFProcessor(file_path=pdf_path, default_metadata={"tag": "upload_manual"})
    documents = processor.extract_documents()
    print(f"      => Encontradas {len(documents)} página(s).")
    
    if len(documents) == 0:
        print("Nenhum texto foi localizado neste PDF. (Talvez seja uma imagem pura e o OCR precisa atuar).")
        sys.exit(1)

    # Passo 2: Chunking (Recorte dos textos)
    print("\n[2/3] Fatiando páginas em chunks RAG (~600 caracteres, 80 overlap)...")
    chunks = split_documents(documents)
    print(f"      => Total de Chunks Semânticos criados: {len(chunks)}")

    # Passo 3: Embedding e Armazenamento Otimizado
    print("\n[3/3] Processando vetores na engine local BGE-M3 e empurrando pro Qdrant DB...")
    start_time = time.time()
    
    qdrant = QdrantAdapter(collection_name="agronomy_docs")
    qdrant.add_documents(chunks)
    
    elapsed = time.time() - start_time
    print(f"      => Sucesso Absoluto! Todos os {len(chunks)} recortes foram fixados no banco em {elapsed:.2f} segundos.")
    print("\n🌐 Abra o seu Dashboard do Docker pra conferir lá dentro: http://localhost:6333/dashboard")

if __name__ == "__main__":
    main()
