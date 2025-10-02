from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/synthesize")
def synthesize(data: dict):
    return {"status": "ok", "result": "synthesized_code"}