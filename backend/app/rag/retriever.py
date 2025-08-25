#!/usr/bin/env python3
"""
Document Retriever for RAG System
Handles document retrieval using vector similarity and fallback methods
"""

from typing import List, Dict, Any, Optional
import logging

from .loader import load_documents
from .embedder import get_embedder

logger = logging.getLogger(__name__)

class DocumentRetriever:
    """Document retriever using vector similarity with fallback to keyword search"""
    
    def __init__(self):
        self.documents = []
        self.embedder = get_embedder()
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure retriever is initialized (lazy initialization)"""
        if not self._initialized:
            self._initialize_retriever()
            self._initialized = True
    
    def _initialize_retriever(self):
        """Initialize the retriever with documents and index"""
        try:
            # Load documents
            self.documents = load_documents()
            logger.info(f"Loaded {len(self.documents)} documents")
            
            # Try to load or create vector index
            if self.embedder.is_available():
                success = self.embedder.load_index()
                if success:
                    logger.info("Vector index loaded successfully")
                else:
                    logger.info("Creating new vector index...")
                    if self.embedder.create_index_from_documents(self.documents):
                        logger.info("Vector index created successfully")
                    else:
                        logger.warning("Failed to create vector index, using fallback search")
            else:
                logger.warning("Vector search not available, using fallback search")
                
        except Exception as e:
            logger.error(f"Error initializing retriever: {e}")
            self.documents = []
    
    def _detect_country_from_query(self, query: str) -> Optional[str]:
        """Detect country from user query using smart keyword matching"""
        query_lower = query.lower()
        
        # Comprehensive country detection keywords
        country_keywords = {
            'usa': ['usa', 'united states', 'america', 'us', 'u.s.', 'u.s.a', 'f-1', 'f1', 'student visa usa', 'american'],
            'uk': ['uk', 'united kingdom', 'britain', 'england', 'tier 4', 'tier4', 'student visa uk', 'british'],
            'australia': ['australia', 'aussie', 'subclass 500', 'student visa australia', 'australian'],
            'south korea': ['south korea', 'korea', 'korean', 'd-2', 'd-4', 'd2', 'd4', 'student visa korea', 'korean student']
        }
        
        # Check for exact country matches first
        for country, keywords in country_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                logger.info(f"🔍 Detected country '{country}' from query: '{query}'")
                return country
        
        # If no direct match, check for visa type patterns
        visa_patterns = {
            'usa': ['f-1', 'f1'],
            'uk': ['tier 4', 'tier4'],
            'australia': ['subclass 500'],
            'south korea': ['d-2', 'd-4', 'd2', 'd4']
        }
        
        for country, patterns in visa_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                logger.info(f"🔍 Detected country '{country}' from visa pattern: '{query}'")
                return country
        
        logger.info(f"❓ No country detected from query: '{query}'")
        return None
    
    def search(self, query: str, top_k: int = 3, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search documents for relevant content with smart country detection
        Args:
            query: Search query
            top_k: Number of results to return
            country: Optional country filter
        Returns:
            List of relevant documents with scores
        """
        # Ensure retriever is initialized
        self._ensure_initialized()
        
        if not self.documents:
            logger.warning("No documents loaded for search")
            return []
        
        # SMART COUNTRY DETECTION
        detected_country = self._detect_country_from_query(query)
        if detected_country and not country:
            country = detected_country
            logger.info(f"🎯 Using detected country: {country}")
        
        # Try vector search first
        if self.embedder.is_available() and hasattr(self.embedder, 'index') and self.embedder.index is not None:
            results = self._vector_search(query, top_k, country)
            if results:
                return results
        
        # Fallback to keyword search
        return self._keyword_search(query, top_k, country)
    
    def _vector_search(self, query: str, top_k: int, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform vector similarity search with country filtering"""
        try:
            # Search using the embedder's search method
            search_results = self.embedder.search(query, top_k * 3)  # Get more for filtering
            
            if not search_results:
                return []
            
            # Format results
            results = []
            for doc in search_results:
                # Extract country from document metadata
                doc_country = doc.get('country', '')
                if not doc_country and 'meta' in doc:
                    doc_country = doc['meta'].get('country', '')
                
                # Filter by country if specified
                if country and doc_country.lower() != country.lower():
                    logger.debug(f"�� Filtering out {doc_country} document for {country} query")
                    continue
                
                results.append({
                    'document': doc,
                    'score': doc.get('score', 0.0),
                    'title': doc.get('title', doc.get('source_file', 'Unknown')),
                    'content': doc.get('content', doc.get('text', '')),
                    'country': doc_country,
                    'source': doc.get('source_file', '')
                })
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"✅ Vector search for '{query}' (country: {country}) returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def _keyword_search(self, query: str, top_k: int, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fallback keyword search using text matching"""
        # Filter by country if specified
        search_docs = self.documents
        if country:
            search_docs = [doc for doc in self.documents if doc.get('country', '').lower() == country.lower()]
        
        # Score documents based on query relevance
        scored_docs = []
        query_terms = query.lower().split()
        
        for doc in search_docs:
            score = self._calculate_relevance_score(doc, query_terms)
            if score > 0:  # Only include relevant documents
                scored_docs.append({
                    'document': doc,
                    'score': score,
                    'title': doc.get('title', doc.get('source_file', 'Unknown')),
                    'content': doc.get('content', doc.get('text', '')),
                    'country': doc.get('country', ''),
                    'source': doc.get('source_file', '')
                })
        
        # Sort by score and return top_k results
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        results = scored_docs[:top_k]
        
        logger.info(f"Keyword search for '{query}' returned {len(results)} results")
        return results
    
    def _calculate_relevance_score(self, doc: Dict[str, Any], query_terms: List[str]) -> float:
        """
        Calculate relevance score for a document (fallback method)
        Higher score = more relevant
        """
        score = 0.0
        
        # Get document text to search
        doc_text = ""
        for field in ['content', 'text', 'question', 'answer', 'description']:
            if field in doc and doc[field]:
                doc_text += " " + str(doc[field])
        
        doc_text = doc_text.lower()
        
        # Score based on term frequency and position
        for term in query_terms:
            if len(term) < 3:  # Skip very short terms
                continue
            
            # Count occurrences
            term_count = doc_text.count(term)
            if term_count > 0:
                score += term_count * 0.5
                
                # Bonus for exact matches
                if term in doc_text:
                    score += 1.0
                
                # Bonus for title matches
                title = doc.get('title', '').lower()
                if term in title:
                    score += 2.0
        
        # Bonus for country-specific queries
        if doc.get('country'):
            country_terms = ['visa', 'study', 'university', 'college', 'education']
            if any(term in doc_text for term in country_terms):
                score += 0.5
        
        return score
    
    def get_search_method(self) -> str:
        """Get the current search method being used"""
        if self.embedder.is_available():
            return "vector_search"
        else:
            return "keyword_search"
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index"""
        return self.embedder.get_index_info()

# Global retriever instance
_retriever = None

def get_retriever() -> DocumentRetriever:
    """Get or create global retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = DocumentRetriever()
    return _retriever

def retrieve(query: str, top_k: int = 3, country: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Main retrieval function
    Args:
        query: Search query
        top_k: Number of results to return
        country: Optional country filter
    Returns:
        List of relevant documents
    """
    try:
        retriever = get_retriever()
        results = retriever.search(query, top_k, country)
        
        # Format results for the chatbot
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result['title'],
                'content': result['content'][:500] + "..." if len(result['content']) > 500 else result['content'],
                'score': result['score'],
                'country': result['country'],
                'source': result['source']
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in retrieval: {e}")
        return []

def search_by_country(query: str, country: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search documents for a specific country
    """
    return retrieve(query, top_k, country)

def get_available_countries() -> List[str]:
    """
    Get list of available countries
    """
    try:
        from .loader import get_available_countries
        return get_available_countries()
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        return []
