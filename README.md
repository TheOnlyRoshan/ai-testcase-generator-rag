AI-powered test case generation from PRD documents using RAG architecture and LLMs.
# AI Test Case Generator (RAG-based)

This project automatically generates **manual test cases from Product Requirement Documents (PRDs)** using a **Retrieval-Augmented Generation (RAG)** pipeline.

The system reads PRD documents, retrieves relevant requirement sections, and uses a Large Language Model (LLM) to generate structured test scenarios.

This tool demonstrates how **AI can assist QA engineers in creating test cases quickly and consistently.**

---

# Problem Statement

Writing test cases from large PRDs is time-consuming and repetitive.

QA engineers must:

- read long requirement documents
- identify test scenarios
- cover edge cases
- structure test cases manually

This project uses **AI + vector search** to automate that workflow.

---

# Architecture
PRD Document (PDF)
-->
Document Loader
-->
Text Chunking
-->
SentenceTransformer Embeddings
-->
FAISS Vector Database
-->
Retriever (RAG)
-->
Gemini LLM
-->
Generated Manual Test Cases

The system retrieves the most relevant requirement sections before asking the LLM to generate test cases.

---

# Tech Stack

- Python
- LangChain
- FAISS (vector database)
- SentenceTransformers (local embeddings)
- Google Gemini API
- HuggingFace Transformers

---

# Project Structure
ai-testcase-generator
│
├── agents
│ └── testcase_agent.py
│
├── loaders
│ └── prd_file_loader.py
│
├── rag
│ ├── text_splitter.py
│ ├── vector_store.py
│ └── embedding_service.py
│
├── prompts
│ └── prompt_templates.py
│
├── config
│ └── settings.py
│
├── main.py
├── requirements.txt
└── README.md


---

# Setup

## 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-testcase-generator-rag.git

cd ai-testcase-generator-rag
---

## 2. Create virtual environment


python -m venv venv
source venv/bin/activate


Windows:


venv\Scripts\activate


---

## 3. Install dependencies


pip install -r requirements.txt


---

## 4. Configure API Key

Create a `.env` file:


GEMINI_API_KEY=your_api_key_here


Get API key from:

https://aistudio.google.com/app/apikey

---

# Usage

Run the application:


python main.py


Enter PRD file path when prompted:


/path/to/prd.pdf


The system will generate test cases automatically.

---

# Example Output


Generated Manual Test Cases

TC01 – User Login with Valid Credentials

Steps:

Open login page
Enter valid username
Enter valid password
Click Login

Expected Result:
User should be successfully logged in.

TC02 – Login with Invalid Password

Steps:

Enter valid username
Enter incorrect password
Click Login

Expected Result:
Error message should be displayed.


---

# Key Features

- PRD-driven test case generation
- Retrieval-Augmented Generation (RAG)
- Local embeddings for efficient retrieval
- Vector search using FAISS
- LLM-powered scenario generation
- Modular architecture

---

# Future Improvements

Planned enhancements:

- Jira integration for automatic story ingestion
- Export generated test cases to CSV / Excel
- Test case deduplication using embeddings
- Automation script generation (Playwright / Selenium)
- Web UI for uploading PRDs
- Support for multiple LLM providers

---

# Use Cases

- QA teams generating test cases from PRDs
- AI-assisted test design
- Requirement validation
- Test coverage analysis

---

# License

MIT License

---

# Author

Roshan Pandey
