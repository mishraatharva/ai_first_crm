from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from src.utils.cache import InteractionLRUCache
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
from src.agent import build_graph
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from dotenv import load_dotenv

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
graph = build_graph()
load_dotenv()

@app.on_event("startup")
def startup_event():
    app.state.cache = InteractionLRUCache(capacity=3)
    app.state.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# React build folder path
frontend_path = os.path.join(os.getcwd(), "frontend", "build")

# Serve static React files
app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

@app.get("/home", response_class=HTMLResponse)
async def serve_home():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Build the React app first by running 'npm run build'</h1>")


class ChatRequest(BaseModel):
    message: str
    state: Optional[Dict] = {}

@app.post("/chat")
def chat(req: ChatRequest):
    print("inside chat route")

    # extract state safely - FIX: Include all frontend state fields
    state = {
        "input": req.message,
        "interaction_data": req.state.get("interaction_data", {}),
        "messages": req.state.get("messages", []),
        "status": req.state.get("status"),
        "followUps": req.state.get("followups", [])  # Note: frontend sends 'followups' (plural)
    }

    result = graph.invoke(state,config={
        "llm": app.state.llm,
        "cache": app.state.cache
    })

    print("🔍 FINAL RESULT:", result)

    return {
        "interaction_data": result.get("interaction_data", {}),
        "messages": result.get("messages", []),
        "status": result.get("status"),
        "missing_data_question": result.get("missing_data_question"),
        "last_id": result.get("last_id"),
        "followups": result.get("followUps", [])
    }