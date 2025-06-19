# Lightweight semantic similarity using sentence-transformers (if available)
# Fallback to no-op if not installed

def get_sentence_embedding(text):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode([text])[0]
    except ImportError:
        return None

def cosine_similarity(vec1, vec2):
    import numpy as np
    if vec1 is None or vec2 is None:
        return 0.0
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def is_semantically_similar(text, goal, threshold=0.6):
    vec1 = get_sentence_embedding(text)
    vec2 = get_sentence_embedding(goal)
    if vec1 is None or vec2 is None:
        return True  # fallback: allow all
    return cosine_similarity(vec1, vec2) >= threshold
