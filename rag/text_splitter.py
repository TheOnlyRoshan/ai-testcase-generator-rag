from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import Settings

class TextSplitter:

    def split(self, documents):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=Settings.CHUNK_SIZE,
            chunk_overlap=Settings.CHUNK_OVERLAP
        )

        chunks = splitter.split_documents(documents)

        return chunks