import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

MAX_TABLE_CHARS = 4000


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Divide documentos de texto corrido em chunks e aplica trava de segurança
    contra tabelas excessivamente grandes.

    Fluxo:
    1. Separa documentos por tipo: texto corrido vs. tabelas (is_table=True).
    2. Texto corrido passa pelo splitter normalmente.
    3. Tabelas dentro do limite (≤ MAX_TABLE_CHARS) são adicionadas intactas —
       dividir uma tabela destrói sua estrutura semântica.
    4. Tabelas acima do limite recebem um "split de emergência" com o mesmo
       splitter do texto — evita OOM/MaxTokenError no modelo de embedding (BGE-M3)
       ao custo de perder parte da estrutura tabular.

    Args:
        documents: Lista de Documents produzidos pelo PDFProcessor.

    Returns:
        Lista de chunks prontos para embedding e indexação no Qdrant.
    """
    splitter = get_text_splitter()

    text_docs:  List[Document] = [d for d in documents if not d.metadata.get("is_table")]
    table_docs: List[Document] = [d for d in documents if d.metadata.get("is_table")]

    chunks: List[Document] = splitter.split_documents(text_docs)

    for table_doc in table_docs:
        size = len(table_doc.page_content)

        if size <= MAX_TABLE_CHARS:
            chunks.append(table_doc)
        else:
            logger.warning(
                f"Tabela grande detectada ({size} chars, limite={MAX_TABLE_CHARS}) "
                f"— página {table_doc.metadata.get('page')}, "
                f"índice {table_doc.metadata.get('table_index')}. "
                f"Aplicando split de emergência."
            )
            emergency_chunks = splitter.split_documents([table_doc])
            chunks.extend(emergency_chunks)

    return chunks
