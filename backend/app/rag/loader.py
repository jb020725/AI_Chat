#!/usr/bin/env python3
"""
Simple Document Loader for RAG System
Loads documents from JSONL files in the data directory
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

# Import centralized paths
from app.utils.paths import CFG, get_country_data_path
from app.utils.helpers import get_file_size_mb

logger = logging.getLogger(__name__)

def load_documents() -> List[Dict[str, Any]]:
    """
    Load all documents from the data directory
    Returns a list of document dictionaries
    """
    documents = []
    data_dir = CFG.DATA_DIR  # Use centralized path
    
    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return documents
    
    # Load documents from JSONL files
    for jsonl_file in data_dir.rglob("*.jsonl"):
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if line.strip():
                            doc = json.loads(line.strip())
                            # Add source information
                            doc['source_file'] = str(jsonl_file)
                            doc['source_line'] = line_num
                            documents.append(doc)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in {jsonl_file}:{line_num}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error reading {jsonl_file}: {e}")
            continue
    
    logger.info(f"Loaded {len(documents)} documents from data directory: {data_dir}")
    return documents

def load_documents_by_country(country: str) -> List[Dict[str, Any]]:
    """
    Load documents for a specific country
    """
    documents = []
    country_data_dir = get_country_data_path(country)  # Use centralized path
    
    if not country_data_dir.exists():
        logger.warning(f"Country data directory not found: {country_data_dir}")
        return documents
    
    # Load documents from JSONL files in country directory
    for jsonl_file in country_data_dir.glob("*.jsonl"):
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if line.strip():
                            doc = json.loads(line.strip())
                            doc['source_file'] = str(jsonl_file)
                            doc['source_line'] = line_num
                            doc['country'] = country
                            documents.append(doc)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in {jsonl_file}:{line_num}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error reading {jsonl_file}: {e}")
            continue
    
    logger.info(f"Loaded {len(documents)} documents for {country} from: {country_data_dir}")
    return documents

def get_available_countries() -> List[str]:
    """
    Get list of available countries with data
    """
    data_dir = CFG.DATA_DIR  # Use centralized path
    countries = []
    
    if data_dir.exists():
        for item in data_dir.iterdir():
            if item.is_dir() and item.name not in ['common', 'index', 'processed', 'sources']:
                countries.append(item.name.title())
    
    logger.info(f"Available countries: {countries}")
    return countries

def get_data_directory_info() -> Dict[str, Any]:
    """
    Get information about data directory structure
    """
    data_dir = CFG.DATA_DIR
    info = {
        "data_directory": str(data_dir),
        "exists": data_dir.exists(),
        "total_size_mb": 0.0,
        "file_count": 0,
        "countries": get_available_countries()
    }
    
    if data_dir.exists():
        for file_path in data_dir.rglob("*.jsonl"):
            info["file_count"] += 1
            info["total_size_mb"] += get_file_size_mb(file_path)
    
    return info