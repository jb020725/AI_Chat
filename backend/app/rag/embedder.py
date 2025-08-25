#!/usr/bin/env python3
"""
Lightweight Embedder for RAG System using GCS + FAISS + Vertex AI
"""

import logging
import os
import pickle
from typing import List, Dict, Any, Optional
import numpy as np

from app.config import settings
from google.cloud import storage
from google.cloud import aiplatform

logger = logging.getLogger(__name__)

class LightweightEmbedder:
    """GCS + FAISS + Vertex AI backed retriever"""
    
    def __init__(self):
        # Initialize Vertex AI
        if not settings.VERTEX_PROJECT_ID:
            raise RuntimeError("VERTEX_PROJECT_ID environment variable is required")
        
        aiplatform.init(project=settings.VERTEX_PROJECT_ID, location=settings.VERTEX_LOCATION)
        
        # GCS configuration
        self.rag_bucket = os.environ.get("RAG_BUCKET", "your-rag-bucket")
        self.index_version = os.environ.get("INDEX_VERSION", "v1")
        self.local_index_dir = os.environ.get("LOCAL_INDEX_DIR", "/tmp/index")
        self.readiness_file = os.environ.get("READINESS_FILE", "/tmp/index/.ready")
        
        # Create local directory
        os.makedirs(self.local_index_dir, exist_ok=True)
        
        # FAISS index and metadata
        self.index = None
        self.meta = None
        
        # Load index at startup
        self._load_index_from_gcs()
    
    def _download_from_gcs(self):
        """Download FAISS index and metadata from GCS"""
        try:
            client = storage.Client()
            bucket = client.bucket(self.rag_bucket)
            
            for name in ["faiss.index", "meta.pkl"]:
                src = f"index/{self.index_version}/{name}"
                dst = os.path.join(self.local_index_dir, name)
                blob = bucket.blob(src)
                
                if not blob.exists():
                    raise FileNotFoundError(f"GCS object missing: gs://{self.rag_bucket}/{src}")
                
                blob.download_to_filename(dst)
                logger.info(f"Downloaded {name} from GCS")
                
        except Exception as e:
            logger.error(f"Failed to download from GCS: {e}")
            raise
    
    def _load_index_from_gcs(self):
        """Load FAISS index and metadata from GCS"""
        try:
            self._download_from_gcs()
            
            # Load FAISS index
            index_path = os.path.join(self.local_index_dir, "faiss.index")
            import faiss
            self.index = faiss.read_index(index_path)
            
            # Load metadata
            meta_path = os.path.join(self.local_index_dir, "meta.pkl")
            with open(meta_path, "rb") as f:
                self.meta = pickle.load(f)
            
            # Mark as ready
            with open(self.readiness_file, "w") as f:
                f.write("ok")
            
            logger.info("Successfully loaded FAISS index and metadata from GCS")
            
        except Exception as e:
            logger.error(f"Failed to load index from GCS: {e}")
            # Don't raise here - allow graceful degradation
    
    def _embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings using Vertex AI text-embedding-004"""
        try:
            from vertexai.language_models import TextEmbeddingModel
            
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            embeddings = model.get_embeddings([text])
            
            # Convert to numpy array and normalize
            vector = np.array(embeddings[0].values, dtype=np.float32)
            vector = vector / (np.linalg.norm(vector) + 1e-12)  # L2 normalize
            
            return vector
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the embedder is ready"""
        return (
            self.index is not None and 
            self.meta is not None and 
            os.path.exists(self.readiness_file)
        )
    
    def create_index_from_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Index creation is managed externally in GCS; noop here"""
        logger.info("Index creation is managed in GCS; skipping local build.")
        return True
    
    def load_index(self) -> bool:
        """Load index from GCS"""
        if not self.is_available():
            self._load_index_from_gcs()
        return self.is_available()
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents using FAISS"""
        if not self.is_available():
            logger.error("Index not available")
            return []
        
        try:
            # Generate query embedding
            query_vector = self._embed_text(query)
            query_vector = query_vector.astype(np.float32).reshape(1, -1)
            
            # Search using FAISS
            scores, ids = self.index.search(query_vector, top_k)
            
            results = []
            for rank, (doc_id, score) in enumerate(zip(ids[0], scores[0])):
                if int(doc_id) < 0:  # FAISS may return -1 for empty index
                    continue
                
                doc_id = int(doc_id)
                if doc_id < len(self.meta.get("texts", [])):
                    result = {
                        "rank": rank + 1,
                        "score": float(score),
                        "content": self.meta["texts"][doc_id],
                        "title": f"Document {doc_id}"
                    }
                    
                    # Add metadata if available
                    if "meta" in self.meta and doc_id < len(self.meta["meta"]):
                        result["meta"] = self.meta["meta"][doc_id]
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get index information"""
        return {
            "status": "gcs_faiss",
            "bucket": self.rag_bucket,
            "version": self.index_version,
            "location": settings.VERTEX_LOCATION,
            "ready": self.is_available(),
            "documents": len(self.meta.get("texts", [])) if self.meta else 0
        }

def get_embedder() -> LightweightEmbedder:
    """Get the lightweight embedder instance"""
    return LightweightEmbedder()