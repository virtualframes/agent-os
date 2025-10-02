from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/prioritize")
def prioritize(data: dict):
    return {"status": "ok", "result": "prioritized_tasks"}