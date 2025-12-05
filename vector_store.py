# --- vector_store.py ---

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance


COLLECTION_NAME = "book_embeddings"

# Rename client instance to avoid conflicts
qdrant_db_client = QdrantClient(path="qdrant_db")


def init_collection():
    try:
        qdrant_db_client.get_collection(collection_name=COLLECTION_NAME)
        print("Collection exists (local).")
    except Exception:
        print("Creating local collection...")
        qdrant_db_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            ,
        )
        print("Collection created (local).")

# End of vector_store.py
