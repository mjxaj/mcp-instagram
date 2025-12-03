from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os

app = FastAPI()

# ------------------------------
# MODELS
# ------------------------------
class SearchRequest(BaseModel):
    query: str
    limit: int = 20

# ------------------------------
# ROOT ENDPOINT
# ------------------------------
@app.get("/")
def home():
    return {"status": "MCP Instagram Server Running"}

# ------------------------------
# MCP DISCOVERY FILE
# ------------------------------
@app.get("/.well-known/mcp.json")
def mcp_file():
    path = os.path.join(".well-known", "mcp.json")
    return FileResponse(path, media_type="application/json")

# ------------------------------
# MCP TOOL ENDPOINT
# ------------------------------
@app.post("/mcp/instagram_search_founders")
async def search_founders(body: SearchRequest):
    # Dummy placeholder
    results = [{
        "username": "demo_user",
        "full_name": "Demo Founder",
        "instagram_url": "https://instagram.com/demo_user",
        "followers": 12345,
        "bio": f"Founder related to: {body.query}"
    }]

    return {"results": results}