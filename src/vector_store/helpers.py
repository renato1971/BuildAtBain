"""Helper functions for Weaviate vector store operations"""

import weaviate
from weaviate.classes.query import Filter
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
import time

load_dotenv(".env", override=True)

outputs_folder = Path(__file__).parent.parent / "outputs"

logger = logging.getLogger(__name__)

# Global client variable
_client = None

def get_weaviate_client():
    """Get or create Weaviate client with lazy initialization and retry logic."""
    global _client
    
    if _client is not None:
        try:
            # Test if connection is still alive
            _client.is_ready()
            return _client
        except Exception:
            logger.warning("Weaviate client connection lost, reconnecting...")
            _client = None
    
    # Get connection details from environment
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    # Parse URL to get host and port
    if "://" in weaviate_url:
        protocol, rest = weaviate_url.split("://", 1)
        http_secure = protocol == "https"
        if ":" in rest:
            http_host = rest.split(":")[0]
            http_port = int(rest.split(":")[1].rstrip("/"))
        else:
            http_host = rest.rstrip("/")
            http_port = 443 if http_secure else 8080
    else:
        http_host = weaviate_url.rstrip("/")
        http_port = 8080
        http_secure = False
    
    grpc_host = http_host
    grpc_port = 50051
    grpc_secure = False
    
    # Retry connection with exponential backoff
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to Weaviate at {http_host}:{http_port} (attempt {attempt + 1}/{max_retries})")
            _client = weaviate.connect_to_custom(
                http_host=http_host,
                http_port=http_port,
                http_secure=http_secure,
                grpc_host=grpc_host,
                grpc_port=grpc_port,
                grpc_secure=grpc_secure
            )
            
            # Test connection
            if _client.is_ready():
                logger.info("Successfully connected to Weaviate")
                return _client
                
        except Exception as e:
            logger.warning(f"Failed to connect to Weaviate: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30s
            else:
                logger.error("Could not connect to Weaviate after maximum retries")
                raise
    
    return _client

# For backward compatibility
client = None


def get_objects_count(collection_name: str) -> int:
    """Get the total number of objects given a collection"""
    
    client = get_weaviate_client()
    collection = client.collections.use(collection_name)

    return collection.aggregate.over_all(total_count=True).total_count


def delete_objects_by_filename(filename_part: str, collection_name: str = "PDFDocument"):
    """Deletes all the objects from the same PDF file given a part of its filename"""
    
    client = get_weaviate_client()
    # set collection
    collection = client.collections.use(collection_name)

    result = collection.data.delete_many(
        where=Filter.by_property("filename").like(f"{filename_part}*"),
        dry_run=False,
        verbose=True
    )
    logger.info(f"Deleted {result.successful} objects with filename like '{filename_part}*'")

def get_data_from_objects(query: str, collection_name: str = "PDFDocument") -> list:
    """Get data from Weaviate given a query string and a collection name"""
    
    client = get_weaviate_client()
    # set collection
    collection = client.collections.get(collection_name)

    results = collection.query.bm25(
        query=query,
        limit=20
    )
    logger.info(f"Query '{query}' returned {len(results.objects)} results from {collection_name}")

    return results.objects

