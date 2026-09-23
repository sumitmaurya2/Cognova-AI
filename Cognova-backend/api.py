from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import run_pipeline
from core.rag_engine import ask_question

app = FastAPI(title="CognovaAI API")


@app.get("/api/ping")
def ping():
    return {"status": "alive"}


# Simple in-memory store (swap for Redis/DB in real production)
sessions = {}


class ProcessRequest(BaseModel):
    source: str
    language: str = "english"


class ChatRequest(BaseModel):
    session_id: str
    question: str


@app.post("/api/process")
def process_meeting(req: ProcessRequest):
    try:
        result = run_pipeline(req.source, req.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    session_id = req.source  # simple for now — improve later (uuid, tied to auth user)
    sessions[session_id] = result["rag_chain"]

    return {
        "session_id": session_id,
        "title": result["title"],
        "summary": result["summary"],
        "action_items": result["action_items"],
        "key_decisions": result["key_decisions"],
        "open_questions": result["open_questions"],
    }


@app.post("/api/chat")
def chat_with_meeting(req: ChatRequest):
    rag_chain = sessions.get(req.session_id)
    if rag_chain is None:
        raise HTTPException(status_code=404, detail="Session not found. Process a meeting first.")

    answer = ask_question(rag_chain, req.question)
    return {"answer": answer}






