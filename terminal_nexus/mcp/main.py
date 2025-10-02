from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

from .router import MCPRouter

app = FastAPI()

import os

# Load sensitive keys from environment variables
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "your-anthropic-api-key")
GATEWAY_URL = "http://127.0.0.1:8080"

mcp_router = MCPRouter(gateway_url=GATEWAY_URL, claude_key=API_KEY)

class CommandRequest(BaseModel):
    command: str
    context: Dict[str, Any]

@app.post("/mcp/route")
async def route_command(request: CommandRequest):
    """
    Receives a command from the gateway and routes it through the MCP.
    """
    response = await mcp_router.route_command(request.command, request.context)
    return response

@app.get("/health")
def health_check():
    return {"ok": True}