from langchain_community.document_loaders import PyPDFLoader

class PRDFileLoader:

    def load(self, file_path):

        loader = PyPDFLoader(file_path)

        docs = loader.load()

        return docs