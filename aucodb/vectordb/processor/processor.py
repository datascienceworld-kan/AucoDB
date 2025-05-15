from typing import List, Dict, Any
from langchain.text_splitter import TextSplitter
from langchain.docstore.document import Document


# Document Processor
class DocumentProcessor:
    def __init__(
        self,
        splitter: TextSplitter,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ):
        self.splitter = splitter
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        if hasattr(self.splitter, "_chunk_size"):
            self.splitter._chunk_size = self.chunk_size
        if hasattr(self.splitter, "_chunk_overlap"):
            self.splitter._chunk_overlap = self.chunk_overlap
        for k, v in kwargs.items():
            if hasattr(self.splitter, k):
                setattr(self.splitter, k, v)

    def process_documents(self, list_texts: List[str]) -> List[Document]:
        documents = [Document(page_content=text) for text in list_texts]
        return self.splitter.split_documents(documents)
