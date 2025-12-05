from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import google.generativeai as genai


# CORRECTED IMPORT: Use the new, unique name
from vector_store import qdrant_db_client, COLLECTION_NAME, init_collection 

# INIT COLLECTION FIRST
init_collection()

# RENAME THE INSTANCE USED IN THE CODE
# For consistency and debugging, let's keep the name simple here
qdrant_client_instance = qdrant_db_client

print("Type of qdrant object:", type(qdrant_client_instance))


# Gemini free model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
chat_model = genai.GenerativeModel("gemini-2.0-flash")
EMBED_MODEL = "models/text-embedding-004"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# RAG Pipeline (Local Qdrant)
# -----------------------------
async def rag_query(user_question: str, selected_text: str = ""):
    print("\nQUESTION:", user_question)

    # Create embedding
    try:
        emb = genai.embed_content(
            model=EMBED_MODEL,
            content=user_question,
            task_type="retrieval_document"
        )
        user_vector = emb["embedding"]
        print("Embedding OK:", len(user_vector))
    except Exception as e:
        print("Embedding error:", e)
        return "Embedding failed."

    try:
        hits = qdrant_client_instance.query_points(
            collection_name=COLLECTION_NAME,
            query=user_vector,
            # using="dense",
            limit=3
        )
        print(f"Qdrant hits: {hits}")
    except Exception as e:
        print("Qdrant search error:", e)
        return "Qdrant search failed."

    

    context = []
    for h in hits.points:
        if h.payload and "text" in h.payload:
            context.append(h.payload["text"])

    print(f"Extracted context: {context}")

    full_context_list = []
    if selected_text:
        full_context_list.append(f"User selected text: {selected_text}")
    if context:
        full_context_list.extend(context)

    full_context_str = "\n\n".join(full_context_list) if full_context_list else "No relevant context found."

    # Generate answer
    prompt = f"""
Use ONLY the following context to answer.

Context:
{full_context_str}

Question: {user_question}

Answer:
"""
    

    # ... (Prompt is generated) ...

    try:
        # 1. Use the synchronous call (no await)
        reply = chat_model.generate_content(prompt)
        
        # 2. Check if the response was blocked for safety reasons
        if not reply.candidates:
            # Check the finish reason of the first candidate (if available)
            finish_reason = reply.prompt_feedback.block_reason.name if reply.prompt_feedback.block_reason else "UNKNOWN"
            print(f"Gemini Safety Block: {finish_reason}")
            return f"The response was blocked by the safety filter (Reason: {finish_reason})."
        
        # If not blocked, return the text
        return reply.text
        
    except Exception as e:
        print("Gemini error:", e)
        return "Failed to generate answer."

# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    question = body.get("message", "")
    selected_text = body.get("selected_text", "")

    if not question:
        return {"reply": "Message is empty."}

    answer = await rag_query(question, selected_text)
    return {"reply": answer}


@app.get("/")
async def root():
    return {"message": "Backend running!"}
