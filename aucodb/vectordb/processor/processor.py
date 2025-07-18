from typing import List, Dict, Any, Optional
from langchain.text_splitter import TextSplitter
from langchain.docstore.document import Document


# Document Processor
class DocumentProcessor:
    def __init__(
        self,
        splitter: TextSplitter,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        **kwargs
    ):
        """
        DocumentProcessor class that updates default attributes of splitter and processes a list of strings or documents.
        Args:
            splitter: TextSplitter object to split documents
            chunk_size: Optional[int] for chunk size. This will override the chunk_size attribute of the splitter
            chunk_overlap: Optional[int] for chunk overlap. This will override the chunk_overlap attribute of the splitter
            **kwargs: Additional keyword arguments to override to the splitter
        """
        self.splitter = splitter
        if hasattr(self.splitter, "_chunk_size") and chunk_size:
            self.splitter._chunk_size = chunk_size
        if hasattr(self.splitter, "_chunk_overlap") and chunk_overlap:
            self.splitter._chunk_overlap = chunk_overlap
        for k, v in kwargs.items():
            if hasattr(self.splitter, k):
                setattr(self.splitter, k, v)

    def process_strings(self, list_texts: List[str]) -> List[Document]:
        """convert a list of strings into documents and split them into chunks
        Args:
            list_texts: List of strings to be processed
        Returns:
            List of Document objects
        """
        documents = [Document(page_content=text) for text in list_texts]
        return self.splitter.split_documents(documents)

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Splits documents into chunks
        Args:
            documents: List of Document objects to be processed
        Returns:
            List of Document objects
        """
        return self.splitter.split_documents(documents)
