from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import google.generativeai as genai
from qdrant_client import QdrantClient

# -----------------------------
# Initialize Qdrant Cloud
# -----------------------------
QDRANT_URL = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "book_embeddings"

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
print("Connected to Qdrant")

# -----------------------------
# Gemini models
# -----------------------------
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
EMBED_MODEL = "models/text-embedding-004"
LLM = genai.GenerativeModel("gemini-2.5-flash-lite")

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# RAG + fallback pipeline
# -----------------------------
async def rag_query(question: str, selected_text: str = ""):
    print("\nQUESTION:", question)

    try:
        # ---------- 1. Create embedding ----------
        emb = genai.embed_content(
            model=EMBED_MODEL,
            content=question
        )
        user_vector = emb["embedding"]
        print("Embedding generated:", len(user_vector))

        # ---------- 2. Query Qdrant ----------
        hits = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=user_vector,
            limit=3
        )
        print("Qdrant hits:", hits)

        # ---------- 3. Extract context ----------
        context = []
        for point in hits.points:
            text = point.payload.get("text", "")
            if text:
                context.append(text)

        if selected_text:
            context.insert(0, f"User selected: {selected_text}")

        full_context = "\n\n".join(context) if context else "No relevant context."

    except Exception as e:
        # ---------- FALLBACK ----------
        print("Embedding/Qdrant error:", e)
        full_context = selected_text if selected_text else "No relevant context."
        print("Fallback: Using LLM directly without embedding/Qdrant.")

    # ---------- 4. Generate answer ----------
    prompt = f"""
Use ONLY the following context to answer.

Context:
{full_context}

Question: {question}

Answer:
"""
    try:
        reply = LLM.generate_content(prompt)
        return reply.text
    except Exception as e:
        print("LLM error:", e)
        return "Failed to generate answer."

# -----------------------------
# API endpoints
# -----------------------------
@app.post("/chat")
async def chat(req: Request):
    data = await req.json()
    msg = data.get("message", "")
    selected = data.get("selected_text", "")

    if not msg:
        return {"reply": "Message is empty."}

    answer = await rag_query(msg, selected)
    return {"reply": answer}

@app.get("/")
async def home():
    return {"message": "Backend OK"}
