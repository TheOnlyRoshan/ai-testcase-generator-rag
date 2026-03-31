import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    MODEL_NAME = "gemini-2.5-flash"