# --- vector_store.py ---

import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

COLLECTION_NAME = "book_embeddings"
VECTOR_NAME = "default"  # default vector name in cloud

# Initialize Qdrant Cloud client
QDRANT_URL = os.getenv("QDRANT_HOST")      # Your cloud URL
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # Your cloud API key

qdrant_db_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
print("Type of qdrant object:", type(qdrant_db_client))

def init_collection():
    """
    For cloud: check if collection exists. Do NOT recreate it.
    """
    try:
        qdrant_db_client.get_collection(collection_name=COLLECTION_NAME)
        print("Collection exists (cloud).")
    except Exception as e:
        print("Error accessing collection:", e)
        print("Please make sure the collection exists in Qdrant Cloud.")
