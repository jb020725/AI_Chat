"""
RAG (Retrieval-Augmented Generation) System
Standard architecture with separate loader, embedder, and retriever modules
"""

from .loader import load_documents, load_documents_by_country, get_available_countries
from .embedder import LightweightEmbedder
from .retriever import retrieve, search_by_country, get_retriever, DocumentRetriever

# Create a get_embedder function that returns the LightweightEmbedder
def get_embedder():
    """Get the embedder instance"""
    return LightweightEmbedder()

__all__ = [
    # Loader functions
    'load_documents',
    'load_documents_by_country', 
    'get_available_countries',
    
    # Embedder
    'get_embedder',
    'LightweightEmbedder',
    
    # Retriever functions
    'retrieve',
    'search_by_country',
    'get_retriever',
    'DocumentRetriever'
]
