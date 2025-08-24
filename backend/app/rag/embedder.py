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
from app.config import settings

# Optional TF-IDF fallback
try:
	from sklearn.feature_extraction.text import TfidfVectorizer
	from sklearn.metrics.pairwise import cosine_similarity
	SKLEARN_AVAILABLE = True
except Exception:
	SKLEARN_AVAILABLE = False
	logging.warning("scikit-learn not available; TF-IDF fallback disabled")

# Optional GCS helper
try:
	from app.utils import gcs as gcs_helper
	GCS_HELPER_AVAILABLE = True
except Exception:
	GCS_HELPER_AVAILABLE = False
	logging.warning("GCS helper not available; local disk persistence only")

# Try to import FAISS and sentence transformers
try:
	import faiss
	from sentence_transformers import SentenceTransformer
	FAISS_AVAILABLE = True
except ImportError:
	FAISS_AVAILABLE = False
	logging.warning("FAISS not available, embedding functionality disabled - using fallback search")

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
		# TF-IDF fallback attributes
		self.tfidf_vectorizer = None
		self.tfidf_matrix = None
		self.tfidf_vectorizer_path = str(index_path).replace('.faiss', '_tfidf.pkl')
		self.tfidf_texts_path = str(index_path).replace('.faiss', '_tfidf_texts.pkl')
		
		if FAISS_AVAILABLE:
			self._initialize_model()
		else:
			logger.warning("Embedding model not available - FAISS or sentence-transformers not installed; will use TF-IDF if available")
	
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
		return self.embedding_model is not None or (SKLEARN_AVAILABLE and self.tfidf_vectorizer is not None)
	
	def create_index_from_documents(self, documents: List[Dict[str, Any]]) -> bool:
		"""
		Create FAISS index from documents
		Args:
			documents: List of document dictionaries
		Returns:
			bool: True if successful, False otherwise
		"""
		if not (FAISS_AVAILABLE and self.embedding_model):
			if SKLEARN_AVAILABLE:
				return self._create_tfidf_index(documents)
			logger.error("Cannot create index - neither FAISS nor TF-IDF available")
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
	
	def _create_tfidf_index(self, documents: List[Dict[str, Any]]) -> bool:
		"""Create a lightweight TF-IDF index and persist to GCS or disk."""
		try:
			texts = []
			kept_docs = []
			for doc in documents:
				text = self._extract_text(doc)
				if text.strip():
					texts.append(text)
					kept_docs.append(doc)
			if not texts:
				logger.warning("No documents contained text for TF-IDF index")
				return False
			if not SKLEARN_AVAILABLE:
				logger.error("scikit-learn not available for TF-IDF index")
				return False
			self.tfidf_vectorizer = TfidfVectorizer(max_features=20000)
			self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
			self.documents = kept_docs
			self._persist_state_tfidf(texts)
			logger.info(f"TF-IDF index created with {len(kept_docs)} docs and {self.tfidf_matrix.shape[1]} features")
			return True
		except Exception as e:
			logger.error(f"Error creating TF-IDF index: {e}")
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
	
	def _persist_state_tfidf(self, texts: List[str]) -> None:
		"""Persist TF-IDF artifacts to disk and optionally to GCS."""
		try:
			# Save locally
			CFG.INDEX_DIR.mkdir(parents=True, exist_ok=True)
			with open(self.tfidf_vectorizer_path, 'wb') as f:
				pickle.dump(self.tfidf_vectorizer, f)
			with open(self.tfidf_texts_path, 'wb') as f:
				pickle.dump(texts, f)
			# Upload to GCS
			if settings.GCS_ENABLED and settings.GCS_BUCKET and GCS_HELPER_AVAILABLE:
				try:
					with open(self.tfidf_vectorizer_path, 'rb') as f:
						gcs_helper.upload_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/tfidf_vectorizer.pkl", f.read(), content_type="application/octet-stream")
					with open(self.tfidf_texts_path, 'rb') as f:
						gcs_helper.upload_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/tfidf_texts.pkl", f.read(), content_type="application/octet-stream")
					logger.info("Uploaded TF-IDF artifacts to GCS")
				except Exception as ge:
					logger.warning(f"Failed to upload TF-IDF artifacts to GCS: {ge}")
		except Exception as e:
			logger.warning(f"Failed persisting TF-IDF artifacts: {e}")
	
	def _load_tfidf_from_gcs(self) -> bool:
		"""Attempt to load TF-IDF artifacts from local disk or GCS."""
		try:
			# Try local first
			if os.path.exists(self.tfidf_vectorizer_path) and os.path.exists(self.tfidf_texts_path):
				with open(self.tfidf_vectorizer_path, 'rb') as f:
					self.tfidf_vectorizer = pickle.load(f)
				with open(self.tfidf_texts_path, 'rb') as f:
					texts = pickle.load(f)
				self.tfidf_matrix = self.tfidf_vectorizer.transform(texts)
				self.documents = [{'text': t} for t in texts]
				logger.info("Loaded TF-IDF artifacts from local disk")
				return True
			# Try GCS
			if settings.GCS_ENABLED and settings.GCS_BUCKET and GCS_HELPER_AVAILABLE:
				vec_bytes = gcs_helper.download_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/tfidf_vectorizer.pkl")
				texts_bytes = gcs_helper.download_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/tfidf_texts.pkl")
				if vec_bytes and texts_bytes:
					with open(self.tfidf_vectorizer_path, 'wb') as f:
						f.write(vec_bytes)
					with open(self.tfidf_texts_path, 'wb') as f:
						f.write(texts_bytes)
					self.tfidf_vectorizer = pickle.loads(vec_bytes)
					texts = pickle.loads(texts_bytes)
					self.tfidf_matrix = self.tfidf_vectorizer.transform(texts)
					self.documents = [{'text': t} for t in texts]
					logger.info("Loaded TF-IDF artifacts from GCS")
					return True
			logger.warning("No TF-IDF artifacts found locally or in GCS")
			return False
		except Exception as e:
			logger.warning(f"Failed loading TF-IDF artifacts: {e}")
			return False
	
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
			# Upload to GCS if configured
			if settings.GCS_ENABLED and settings.GCS_BUCKET and GCS_HELPER_AVAILABLE:
				try:
					with open(self.index_path, 'rb') as f:
						gcs_helper.upload_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/visa_vectors.faiss", f.read(), content_type="application/octet-stream")
					with open(self.documents_path, 'rb') as f:
						gcs_helper.upload_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/visa_vectors_docs.pkl", f.read(), content_type="application/octet-stream")
					logger.info("Uploaded FAISS index and docs to GCS")
				except Exception as ge:
					logger.warning(f"Failed to upload FAISS index to GCS: {ge}")
			return True
			
		except Exception as e:
			logger.error(f"Error saving index: {e}")
			return False
	
	def load_index(self) -> bool:
		"""Load existing FAISS index"""
		try:
			local_index_exists = os.path.exists(self.index_path) and os.path.exists(self.documents_path)
			if not local_index_exists and settings.GCS_ENABLED and settings.GCS_BUCKET and GCS_HELPER_AVAILABLE:
				# Try fetching FAISS from GCS
				idx_bytes = gcs_helper.download_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/visa_vectors.faiss")
				docs_bytes = gcs_helper.download_bytes(settings.GCS_BUCKET, f"{settings.GCS_INDEX_PREFIX}/visa_vectors_docs.pkl")
				if idx_bytes and docs_bytes:
					Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
					with open(self.index_path, 'wb') as f:
						f.write(idx_bytes)
					with open(self.documents_path, 'wb') as f:
						f.write(docs_bytes)
					logger.info("Downloaded FAISS index and docs from GCS")
			if not os.path.exists(self.index_path) or not os.path.exists(self.documents_path):
				logger.warning("FAISS index not found locally or in GCS; trying TF-IDF fallback load")
				return self._load_tfidf_from_gcs()
			
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
			return self._load_tfidf_from_gcs()
	
	def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
		"""Search for similar documents"""
		if not (self.index and self.embedding_model):
			# TF-IDF path
			if self.tfidf_vectorizer is not None and self.tfidf_matrix is not None and hasattr(self, 'documents'):
				try:
					q_vec = self.tfidf_vectorizer.transform([query])
					sims = cosine_similarity(q_vec, self.tfidf_matrix).ravel()
					top_idx = np.argsort(-sims)[:top_k]
					results = []
					for rank, idx in enumerate(top_idx, start=1):
						if idx < len(self.documents):
							doc = self.documents[idx].copy()
							doc['similarity_score'] = float(sims[idx])
							doc['rank'] = rank
							results.append(doc)
					return results
				except Exception as e:
					logger.error(f"TF-IDF search error: {e}")
					return []
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
		if not (self.index or self.tfidf_matrix is not None):
			return {"status": "no_index", "message": "No index loaded"}
		
		return {
			"status": "loaded",
			"total_vectors": getattr(self.index, 'ntotal', self.tfidf_matrix.shape[0] if self.tfidf_matrix is not None else 0),
			"dimension": getattr(self.index, 'd', self.tfidf_matrix.shape[1] if self.tfidf_matrix is not None else 0),
			"index_type": str(type(self.index)) if self.index is not None else "TFIDF",
			"model_name": self.model_name,
			"index_path": self.index_path,
			"documents_count": len(self.documents) if hasattr(self, 'documents') else 0
		}


def get_embedder() -> DocumentEmbedder:
	"""Get embedder instance with default configuration"""
	return DocumentEmbedder()