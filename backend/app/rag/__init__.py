"""
RAG (Retrieval-Augmented Generation) System
Standard architecture with separate loader, embedder, and retriever modules
"""

from .loader import load_documents, load_documents_by_country, get_available_countries
from .embedder import get_embedder, DocumentEmbedder
from .retriever import retrieve, search_by_country, get_retriever, DocumentRetriever

__all__ = [
    # Loader functions
    'load_documents',
    'load_documents_by_country', 
    'get_available_countries',
    
    # Embedder
    'get_embedder',
    'DocumentEmbedder',
    
    # Retriever functions
    'retrieve',
    'search_by_country',
    'get_retriever',
    'DocumentRetriever'
]
