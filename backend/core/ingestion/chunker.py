from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document

def get_text_splitter() -> RecursiveCharacterTextSplitter:
    # Parametrização aprovada no relatorio Brainstorming (600 tokens/overlap 80)
    return RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

def split_documents(documents: List[Document]) -> List[Document]:
    splitter = get_text_splitter()
    return splitter.split_documents(documents)
