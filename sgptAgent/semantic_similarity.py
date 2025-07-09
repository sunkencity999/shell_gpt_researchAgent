# Use the same Ollama client and embedding model as the main agent
# to ensure consistency and avoid external dependencies.

from sgptAgent.llm_functions.ollama import OllamaClient
from sgptAgent.config import cfg
import numpy as np

# Cache the client and model name
_ollama_client = None
_embedding_model = None

def _get_client_and_model():
    global _ollama_client, _embedding_model
    if _ollama_client is None:
        _ollama_client = OllamaClient()
        _embedding_model = cfg.get("EMBEDDING_MODEL")
    return _ollama_client, _embedding_model

def get_sentence_embedding(text: str):
    client, model_name = _get_client_and_model()
    if client is None or model_name is None:
        return None
    try:
        return client.get_embedding(model_name, text)
    except Exception as e:
        print(f"Error getting embedding from Ollama: {e}")
        return None

def cosine_similarity(vec1, vec2):
    if vec1 is None or vec2 is None or not hasattr(vec1, '__len__') or not hasattr(vec2, '__len__') or len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    # Ensure they are numpy arrays for dot product
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def is_semantically_similar(text: str, goal: str, threshold: float = 0.6) -> bool:
    vec1 = get_sentence_embedding(text)
    vec2 = get_sentence_embedding(goal)
    if vec1 is None or vec2 is None:
        # If embedding fails, default to a keyword-based check as a fallback.
        text_words = set(text.lower().split())
        goal_words = set(goal.lower().split())
        if not goal_words:
            return False
        common_words = text_words.intersection(goal_words)
        # A simple keyword overlap check
        return (len(common_words) / len(goal_words)) > 0.1 if goal_words else False
        
    return cosine_similarity(vec1, vec2) >= threshold