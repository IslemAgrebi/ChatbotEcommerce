import json
import os
import requests
from uuid import uuid4
from fastapi import FastAPI
from dto.dto import SearchRequest
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from prompt.template import PROMPT_TEMPLATE

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

app = FastAPI()

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

with open("data/data.json", "r") as file:
    data = json.load(file)

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)

documents = [
    Document(
        page_content=f"{q['question']}\n{q['answer']}",
        metadata={"source": "FAQ"},
    )
    for q in data["questions"]
]

uuids = [str(uuid4()) for _ in range(len(documents))]
vector_store.add_documents(documents=documents, ids=uuids)

@app.post("/generate_with_gemini")
async def generate_with_gemini(request: SearchRequest):
    try:
        results = vector_store.similarity_search(
            query=request.query,
            k=request.k,
            filter={"source": request.source},
        )

        if not results:
            return {"status": "error", "message": "No relevant results found."}

        retrieved_texts = "\n\n".join([res.page_content for res in results])

        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": PROMPT_TEMPLATE}
                        ]
                    }
                ]
            }
        )

        if response.status_code == 200:
            gemini_response = response.json()
            return {
                "status": "success",
                "query": request.query,
                "retrieved_results": results,
                "gemini_response": gemini_response,
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to call Gemini API: {response.text}",
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
