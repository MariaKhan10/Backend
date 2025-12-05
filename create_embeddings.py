import os
from glob import glob
from dotenv import load_dotenv
import qdrant_client
from qdrant_client.models import VectorParams, Distance, PointStruct
import google.generativeai as genai
from tqdm import tqdm  # for progress bar

load_dotenv()

# -----------------------------
# Load ENV
# -----------------------------
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "book_embeddings") # Default to book_embeddings
EMBEDDING_SIZE = 768 # Force to 768 to match text-embedding-004

# Gemini Config
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
EMBED_MODEL = "models/text-embedding-004"

# -----------------------------
# Qdrant Client (Local)
# -----------------------------
client = qdrant_client.QdrantClient(path="qdrant_db") # Use local path

# -----------------------------
# Create Collection (recreates every time)
# -----------------------------
print(f"Recreating collection '{COLLECTION_NAME}'...")
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=EMBEDDING_SIZE,
        distance=Distance.COSINE
    )
)
print("Collection created successfully.\n")

# -----------------------------
# Read all .md files recursively
# -----------------------------
DOCS_PATH = "docs/**/*.md"
files = glob(DOCS_PATH, recursive=True)

points = []
pid = 1

print(f"Found {len(files)} markdown files. Generating embeddings...\n")

for file in tqdm(files, desc="Embedding files", unit="file"):
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    # Log current file
    print(f"Embedding file: {file}")

    # Create Gemini Embedding
    emb = genai.embed_content(
        model=EMBED_MODEL,
        content=text
    )

    vector = emb["embedding"]

    points.append(
        PointStruct(
            id=pid,
            vector=vector,
            payload={
                "text": text,
                "file_path": file
            }
        )
    )
    pid += 1

# Upload to Qdrant
print("\nUploading embeddings to Qdrant...")
client.upsert(
    collection_name=COLLECTION_NAME,
    points=points
)

print(f"\nSuccessfully uploaded {len(points)} documents to '{COLLECTION_NAME}'!")
