from sentence_transformers import SentenceTransformer

class Vectorier:
    def __init__(self):
        self.model = SentenceTransformer("deepvk/USER-bge-m3")

    def get_vector(self, text: str) -> list[float]:    
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    