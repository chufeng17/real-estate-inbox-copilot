import json
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import models
from app.core import llm

class VectorStore:
    def __init__(self, db: Session):
        self.db = db

    def upsert_embedding(self, entity_type: str, entity_id: int, text: str, metadata: Dict[str, Any] = None):
        """
        Generates an embedding for the text using Google Gemini and stores it.
        """
        try:
            embedding_vector = llm.generate_embedding(text)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Fallback to mock or empty if API fails (or re-raise depending on requirements)
            # For now, let's just log and return to avoid crashing the whole ingestion
            return

        # Check if exists
        existing = self.db.query(models.Embedding).filter(
            models.Embedding.entity_type == entity_type,
            models.Embedding.entity_id == entity_id
        ).first()

        if existing:
            existing.embedding = json.dumps(embedding_vector)
            existing.metadata_json = metadata
            self.db.add(existing)
        else:
            new_embedding = models.Embedding(
                entity_type=entity_type,
                entity_id=entity_id,
                embedding=json.dumps(embedding_vector),
                metadata_json=metadata
            )
            self.db.add(new_embedding)
        
        self.db.commit()

    def search(self, query: str, entity_type: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for similar entities using cosine similarity.
        """
        try:
            query_vector = llm.generate_embedding(query)
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []
        
        filters = []
        if entity_type:
            filters.append(models.Embedding.entity_type == entity_type)
            
        candidates = self.db.query(models.Embedding).filter(*filters).all()
        
        results = []
        for cand in candidates:
            try:
                cand_vec = json.loads(cand.embedding)
                score = self._cosine_similarity(query_vector, cand_vec)
                results.append({
                    "entity_type": cand.entity_type,
                    "entity_id": cand.entity_id,
                    "score": score,
                    "metadata": cand.metadata_json
                })
            except Exception as e:
                print(f"Error processing candidate {cand.id}: {e}")
                continue
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def clear_all(self):
        """
        Clear all embeddings from the vector store.
        Used for demo reset.
        """
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            deleted_count = db.query(models.Embedding).delete()
            db.commit()
            return deleted_count
        finally:
            db.close()
