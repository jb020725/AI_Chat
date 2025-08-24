#!/usr/bin/env python3
"""
Document Embedder for RAG System
Handles text embedding and FAISS index management
"""

import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np

# Import centralized paths
from app.utils.paths import CFG, get_index_file_path

# Try to import FAISS and sentence transformers
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, embedding functionality disabled")

logger = logging.getLogger(__name__)

class DocumentEmbedder:
    """Handles document embedding and FAISS index management"""
    
    def __init__(self, index_path: str = None, model_name: str = "all-MiniLM-L6-v2"):
        # Use centralized path for index files
        if index_path is None:
            index_path = get_index_file_path("visa_vectors.faiss")
        else:
            # If custom path provided, ensure it's in the index directory
            index_path = CFG.INDEX_DIR / Path(index_path).name
            
        self.index_path = str(index_path)
        self.documents_path = str(index_path).replace('.faiss', '_docs.pkl')
        self.model_name = model_name
        self.embedding_model = None
        self.index = None
        
        if FAISS_AVAILABLE:
            self._initialize_model()
        else:
            logger.warning("Embedding model not available - FAISS or sentence-transformers not installed")
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
    
    def is_available(self) -> bool:
        """Check if the embedder is available and ready to use"""
        return self.embedding_model is not None
    
    def create_index_from_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Create FAISS index from documents
        Args:
            documents: List of document dictionaries
        Returns:
            bool: True if successful, False otherwise
        """
        if not FAISS_AVAILABLE or not self.embedding_model:
            logger.error("Cannot create index - embedding model not available")
            return False
        
        if not documents:
            logger.warning("No documents provided for indexing")
            return False
        
        try:
            total_docs = len(documents)
            logger.info(f"Starting vector indexing for {total_docs} documents...")
            logger.info(f"Index will be saved to: {CFG.INDEX_DIR}")
            
            # Group documents by source folder for better progress tracking
            docs_by_folder = {}
            for doc in documents:
                source_file = doc.get('source_file', 'unknown')
                folder = Path(source_file).parent.name
                if folder not in docs_by_folder:
                    docs_by_folder[folder] = []
                docs_by_folder[folder].append(doc)
            
            logger.info(f"Found {len(docs_by_folder)} data folders: {list(docs_by_folder.keys())}")
            
            # Generate embeddings with progress tracking
            embeddings = []
            processed_docs = []
            processed_count = 0
            
            for folder_name, folder_docs in docs_by_folder.items():
                logger.info(f"Processing folder: {folder_name} ({len(folder_docs)} documents)")
                
                for i, doc in enumerate(folder_docs):
                    # Extract text content
                    text = self._extract_text(doc)
                    if text.strip():
                        try:
                            # Show progress every 10 documents or for each document in small folders
                            if len(folder_docs) <= 20 or i % 10 == 0 or i == len(folder_docs) - 1:
                                progress = ((processed_count + i) / total_docs) * 100
                                logger.info(f"  Document {i+1}/{len(folder_docs)} - {progress:.1f}% complete")
                            
                            embedding = self.embedding_model.encode(text)
                            embeddings.append(embedding)
                            processed_docs.append(doc)
                            
                        except Exception as e:
                            logger.error(f"Error processing document {i+1} in {folder_name}: {e}")
                            continue
                    
                    processed_count += 1
            
            if not embeddings:
                logger.error("No valid embeddings generated")
                return False
            
            logger.info("Converting embeddings to numpy array...")
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            logger.info("Creating FAISS index...")
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            logger.info("Normalizing vectors for cosine similarity...")
            faiss.normalize_L2(embeddings_array)
            
            logger.info("Adding vectors to FAISS index...")
            self.index.add(embeddings_array)
            
            logger.info("Saving index and documents...")
            success = self._save_index(processed_docs)
            
            if success:
                logger.info(f"SUCCESS! Created FAISS index with {len(processed_docs)} documents")
                logger.info(f"Index dimension: {dimension}")
                logger.info(f"Saved to: {self.index_path}")
                logger.info(f"Documents saved to: {self.documents_path}")
                return True
            else:
                logger.error("Failed to save index")
                return False
                
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    def _extract_text(self, doc: Dict[str, Any]) -> str:
        """Extract text content from document"""
        # Try different possible text fields
        text_fields = ['text', 'content', 'question', 'answer', 'title']
        
        for field in text_fields:
            if field in doc and doc[field]:
                return str(doc[field])
        
        # If no text field found, try to construct from available fields
        text_parts = []
        for key, value in doc.items():
            if key not in ['source_file', 'source_line', 'country'] and value:
                text_parts.append(str(value))
        
        return " ".join(text_parts)
    
    def _save_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Save FAISS index and documents"""
        try:
            # Ensure index directory exists
            CFG.INDEX_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save documents metadata
            with open(self.documents_path, 'wb') as f:
                pickle.dump(documents, f)
            
            logger.info(f"Index and documents saved successfully to {CFG.INDEX_DIR}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    def load_index(self) -> bool:
        """Load existing FAISS index"""
        try:
            if not os.path.exists(self.index_path):
                logger.warning(f"Index file not found: {self.index_path}")
                return False
            
            if not os.path.exists(self.documents_path):
                logger.warning(f"Documents file not found: {self.documents_path}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load documents
            with open(self.documents_path, 'rb') as f:
                self.documents = pickle.load(f)
            
            logger.info(f"Index loaded successfully from {self.index_path}")
            logger.info(f"Index contains {self.index.ntotal} vectors")
            logger.info(f"Documents loaded: {len(self.documents)}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.index or not self.embedding_model:
            logger.error("Index or model not available")
            return []
        
        try:
            # Encode query
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding, top_k)
            
            # Return results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['similarity_score'] = float(score)
                    doc['rank'] = i + 1
                    results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []

    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index"""
        if not self.index:
            return {"status": "no_index", "message": "No index loaded"}
        
        return {
            "status": "loaded",
            "total_vectors": self.index.ntotal,
            "dimension": self.index.d,
            "index_type": str(type(self.index)),
            "model_name": self.model_name,
            "index_path": self.index_path,
            "documents_count": len(self.documents) if hasattr(self, 'documents') else 0
        }

def get_embedder() -> DocumentEmbedder:
    """Get embedder instance with default configuration"""
    return DocumentEmbedder()