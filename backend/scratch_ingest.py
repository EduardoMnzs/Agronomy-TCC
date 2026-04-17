import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.documents import Document
from infrastructure.vectordb.qdrant_adapter import QdrantAdapter
from core.ingestion.chunker import split_documents

def test_ingestion():
    print("Iniciando Adapter do Qdrant. Essa etapa vai baixar os modelos do SentenceTransformer se for a primeira vez!")
    qdrant = QdrantAdapter(collection_name="test_collection")
    
    docs = [
        Document(
            page_content="A adubacao com cloreto de potassio no Cerrado exige cuidado para evitar salinidade e lixiviacao na soja.",
            metadata={"source": "guia_adubo.pdf", "page": 1}
        ),
        Document(
            page_content="Sistemas RAG ajudam a achar paginas exatas sobre agricultura limitando o top_k.",
            metadata={"source": "tech_doc.pdf", "page": 3}
        )
    ]
    
    chunks = split_documents(docs)
    print(f"Chunks gerados: {len(chunks)}")
    
    qdrant.add_documents(chunks)
    print("Chunks ingeridos no banco com sucesso (in-memory)!")
    
    results = qdrant.similarity_search("Como adubar o cerrado", k=1)
    
    print("\nResultados da Busca:")
    for r in results:
        print(f"-> {r.page_content}")

if __name__ == "__main__":
    test_ingestion()
