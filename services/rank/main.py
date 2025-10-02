from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/rank")
def rank(data: dict):
    return {"status": "ok", "result": "ranked_items"}