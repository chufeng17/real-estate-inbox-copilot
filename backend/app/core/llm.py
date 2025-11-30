import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash-exp")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-004")

if not GOOGLE_API_KEY:
    # Fallback or warning - for now we just print, but in prod should log/error
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=GOOGLE_API_KEY)

def get_model(model_name: str = MODEL_NAME):
    """
    Returns a configured GenerativeModel instance.
    """
    return genai.GenerativeModel(model_name)

def get_embedding_model(model_name: str = EMBEDDING_MODEL_NAME):
    """
    Returns the embedding model name (Gemini SDK uses function calls usually, but this helper can be useful).
    Actually, for embeddings we usually call genai.embed_content directly.
    So this might just return the model name string.
    """
    return model_name

def generate_text(prompt: str, model_name: str = MODEL_NAME) -> str:
    """
    Simple helper to generate text.
    """
    model = get_model(model_name)
    response = model.generate_content(prompt)
    return response.text

def generate_embedding(text: str, model_name: str = EMBEDDING_MODEL_NAME) -> list[float]:
    """
    Helper to generate embeddings.
    """
    result = genai.embed_content(
        model=model_name,
        content=text,
        task_type="retrieval_document",
        title="Embedding"
    )
    return result['embedding']
