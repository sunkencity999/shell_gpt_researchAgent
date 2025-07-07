# Lightweight semantic similarity using sentence-transformers (if available)
# Fallback to no-op if not installed

_model_cache = None

def _get_model():
    global _model_cache
    if _model_cache is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model_cache = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            _model_cache = None
    return _model_cache

def get_sentence_embedding(text):
    model = _get_model()
    if model is None:
        return None
    return model.encode([text])[0]

def cosine_similarity(vec1, vec2):
    import numpy as np
    if vec1 is None or vec2 is None or not hasattr(vec1, '__len__') or not hasattr(vec2, '__len__') or len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def is_semantically_similar(text, goal, threshold=0.6):
    vec1 = get_sentence_embedding(text)
    vec2 = get_sentence_embedding(goal)
    if vec1 is None or vec2 is None:
        return True  # fallback: allow all
    return cosine_similarity(vec1, vec2) >= threshold
