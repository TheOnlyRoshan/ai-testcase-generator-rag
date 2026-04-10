import os
from loaders.prd_file_loader import PRDFileLoader
from rag.text_splitter import TextSplitter
from rag.vector_store import VectorStore
from agents.testcase_agent import TestCaseAgent


# Hardcoded PRD file path
PRD_PATH = "/Users/roshanpandey/Downloads/PRD_ SquadSweat (MVP).pdf"


def main():

    print("\nAI Test Case Generator\n")

    file_path = PRD_PATH

    # Validate path
    if not os.path.exists(file_path):
        print("\nERROR: File not found.")
        print("Please check the path and try again.\n")
        return

    try:

        # Step 1 — Load PRD
        print("\nLoading PRD document...")
        loader = PRDFileLoader()
        docs = loader.load(file_path)

        # Step 2 — Split into chunks
        print("Splitting document into chunks...")
        splitter = TextSplitter()
        chunks = splitter.split(docs)

        print(f"Total chunks created: {len(chunks)}")

        # Step 3 — Create Vector DB
        print("Creating vector database...")
        vector_db = VectorStore().create(chunks)

        # Step 4 — Create Retriever
        retriever = vector_db.as_retriever(
            search_kwargs={"k": 4}
        )

        # Step 5 — Retrieve relevant context
        print("Retrieving relevant document sections...")

        relevant_docs = retriever.invoke(
            "Generate comprehensive manual test cases from the PRD"
        )

        context = "\n".join(
            [doc.page_content for doc in relevant_docs]
        )

        # Limit context size (prevents token overflow)
        context = context[:8000]

        # Step 6 — Generate Test Cases
        print("Generating test cases using AI...\n")

        agent = TestCaseAgent()
        testcases = agent.generate(context)

        print("========================================")
        print("Generated Manual Test Cases")
        print("========================================\n")

        print(testcases)

        print("\n========================================")
        print("Generation completed successfully\n")

    except Exception as e:

        print("\nAn error occurred while generating test cases:")
        print(str(e))


if __name__ == "__main__":
    main()