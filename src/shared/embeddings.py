import numpy as np
from typing import List, Optional
from pathlib import Path
import pickle
from .logger import get_logger
from .error_handler import handle_errors, retry_with_backoff

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Optional[str] = None):
        self.model_name = model_name
        self.model = None
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_cache = {}
        
        logger.info("EmbeddingService initialized", model=model_name)
    
    def _load_model(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading embedding model", model=self.model_name)
                self.model = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error("Failed to load embedding model", error=str(e))
                raise
    
    @retry_with_backoff(max_retries=2)
    @handle_errors(fallback_value=None)
    def encode(self, text: str) -> Optional[np.ndarray]:
        if not text or not text.strip():
            return None
        
        cache_key = hash(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        self._load_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        self._embedding_cache[cache_key] = embedding
        
        logger.debug("Text encoded", text_length=len(text), embedding_dim=len(embedding))
        return embedding
    
    @handle_errors(fallback_value=[])
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        if not texts:
            return []
        
        self._load_model()
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        
        logger.info("Batch encoded", count=len(texts), batch_size=batch_size)
        return list(embeddings)
    
    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        if emb1 is None or emb2 is None:
            return 0.0
        
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        threshold: float = 0.75,
    ) -> List[int]:
        if query_embedding is None or not candidate_embeddings:
            return []
        
        similar_indices = []
        for idx, candidate_emb in enumerate(candidate_embeddings):
            if candidate_emb is None:
                continue
            
            similarity = self.cosine_similarity(query_embedding, candidate_emb)
            if similarity >= threshold:
                similar_indices.append(idx)
        
        return similar_indices
    
    def cluster_by_similarity(
        self,
        texts: List[str],
        threshold: float = 0.75,
    ) -> List[List[int]]:
        if not texts:
            return []
        
        embeddings = self.encode_batch(texts)
        clusters = []
        assigned = set()
        
        for i, emb_i in enumerate(embeddings):
            if i in assigned or emb_i is None:
                continue
            
            cluster = [i]
            assigned.add(i)
            
            for j, emb_j in enumerate(embeddings[i+1:], start=i+1):
                if j in assigned or emb_j is None:
                    continue
                
                similarity = self.cosine_similarity(emb_i, emb_j)
                if similarity >= threshold:
                    cluster.append(j)
                    assigned.add(j)
            
            clusters.append(cluster)
        
        logger.info(
            "Clustering complete",
            input_count=len(texts),
            cluster_count=len(clusters),
            threshold=threshold,
        )
        
        return clusters
    
    def save_cache(self):
        cache_file = self.cache_dir / "embedding_cache.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self._embedding_cache, f)
            logger.info("Embedding cache saved", size=len(self._embedding_cache))
        except Exception as e:
            logger.error("Failed to save cache", error=str(e))
    
    def load_cache(self):
        cache_file = self.cache_dir / "embedding_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    self._embedding_cache = pickle.load(f)
                logger.info("Embedding cache loaded", size=len(self._embedding_cache))
            except Exception as e:
                logger.error("Failed to load cache", error=str(e))
                self._embedding_cache = {}

embedding_service = EmbeddingService()
