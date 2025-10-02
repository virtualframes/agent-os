# token_optimizer/main.py
# Centralized service for tracking and enforcing LLM token usage budgets.

import os
from fastapi import FastAPI
from pydantic import BaseModel
from databases import Database

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://agentos:password@localhost/token_optimizer_db"
)

database = Database(DATABASE_URL)

# SQL Schema Definition
# ----------------------
# CREATE TABLE IF NOT EXISTS token_usage_logs (
#     id SERIAL PRIMARY KEY,
#     trace_id TEXT NOT NULL,
#     user_id TEXT NOT NULL,
#     model_name TEXT NOT NULL,
#     input_tokens INTEGER NOT NULL,
#     output_tokens INTEGER NOT NULL,
#     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
# );


# --- Models ---
class TokenUsage(BaseModel):
    trace_id: str
    model_name: str
    input_tokens: int
    output_tokens: int
    user_id: str


class BudgetCheck(BaseModel):
    user_id: str
    estimated_tokens: int


# --- Application ---
app = FastAPI(title="Token Optimizer Service")


@app.on_event("startup")
async def startup_event():
    """Connect to the PostgreSQL database when the application starts."""
    await database.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from the PostgreSQL database on shutdown."""
    await database.disconnect()


@app.post("/v1/usage/track")
async def track_usage(usage: TokenUsage):
    """
    Receives token usage data and logs it to the database.
    This is a fire-and-forget endpoint.
    """
    print(
        f"[{usage.trace_id}] Tracking usage for user {usage.user_id}: "
        f"{usage.input_tokens + usage.output_tokens} tokens on {usage.model_name}"
    )

    query = (
        "INSERT INTO token_usage_logs (trace_id, user_id, model_name, input_tokens, output_tokens) "
        "VALUES (:trace_id, :user_id, :model_name, :input_tokens, :output_tokens)"
    )

    await database.execute(
        query,
        values={
            "trace_id": usage.trace_id,
            "user_id": usage.user_id,
            "model_name": usage.model_name,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
        },
    )

    return {"status": "logged"}


@app.post("/v1/budget/check")
async def check_budget(check: BudgetCheck):
    """
    Checks if a user has enough budget for an estimated number of tokens.
    """
    print(
        f"Checking budget for user {check.user_id} for {check.estimated_tokens} tokens."
    )

    query = (
        "SELECT COUNT(*) AS usage_count FROM token_usage_logs WHERE user_id = :user_id"
    )
    result = await database.fetch_one(query, values={"user_id": check.user_id})
    usage_count = result["usage_count"] if result is not None else 0

    # TODO: Implement real budget logic using usage_count and estimated_tokens.
    return {"allow": True, "usage_count": usage_count}
