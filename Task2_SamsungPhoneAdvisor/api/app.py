import os
import sys
import traceback
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from nlu.nlu import parse_question
from retriever.retriever import retrieve_from_db
from generator.generator import generate_final_answer

app = FastAPI(title="Samsung Phone Advisor")

static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

class AskRequest(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask_question(request: AskRequest):
    try:
        parsed = parse_question(request.question)
        retrieved = retrieve_from_db(parsed)
        answer = generate_final_answer(retrieved, parsed)
        return {"answer": answer}
    except Exception as e:
        traceback.print_exc()
        return {"answer": f"⚠️ Internal Error: {e}"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8010))
    uvicorn.run("api.app:app", host="127.0.0.1", port=port, reload=True)
