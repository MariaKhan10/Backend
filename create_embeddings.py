import os
from glob import glob
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import google.generativeai as genai
from tqdm import tqdm  # progress bar

# Load environment variables
load_dotenv()

# -----------------------------
# Config
# -----------------------------
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "book_embeddings")
EMBEDDING_SIZE = 768  # Matches text-embedding-004

# Gemini Config
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
EMBED_MODEL = "models/text-embedding-004"

# -----------------------------
# Qdrant Cloud Client
# -----------------------------
QDRANT_URL = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
print("Type of Qdrant object:", type(client))

# -----------------------------
# Check collection
# -----------------------------
try:
    client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' exists. Skipping creation.")
except Exception as e:
    print(f"Collection '{COLLECTION_NAME}' does not exist. Creating it now...")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_SIZE,
            distance=Distance.COSINE
        )
    )
    print("Collection created successfully.\n")

# -----------------------------
# Read all markdown files
# -----------------------------
DOCS_PATH = "docs/**/*.md"
files = glob(DOCS_PATH, recursive=True)

points = []
pid = 1

print(f"Found {len(files)} markdown files. Generating embeddings...\n")

for file in tqdm(files, desc="Embedding files", unit="file"):
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"Embedding file: {file}")

    # Create Gemini embedding
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

# -----------------------------
# Upload to Cloud
# -----------------------------
if points:
    print("\nUploading embeddings to Qdrant Cloud...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"\nSuccessfully uploaded {len(points)} documents to '{COLLECTION_NAME}'!")
else:
    print("No files to upload.")
