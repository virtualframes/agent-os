from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/scan/code")
def scan_code(data: dict):
    return {"status": "ok", "result": "scan_results"}

@app.post("/scan/deps")
def scan_deps(data: dict):
    return {"status": "ok", "result": "dependency_scan_results"}