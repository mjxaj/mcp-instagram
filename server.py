from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_PATH = os.path.join(BASE_DIR, ".well-known", "mcp.json")


@app.get("/")
def root():
    return {"status": "MCP Instagram Server is running"}


@app.get("/.well-known/mcp.json")
def serve_mcp():
    if not os.path.exists(MCP_PATH):
        return {"error": "mcp.json not found at .well-known/mcp.json"}

    with open(MCP_PATH, "r") as f:
        data = json.load(f)
    return Response(content=json.dumps(data), media_type="application/json")


# Example MCP tool
@app.get("/mcp/instagram_search_founders")
def instagram_search(query: str = "founder", limit: int = 10):
    return {
        "results": [
            {
                "username": "test_user",
                "full_name": "Test User",
                "instagram": "https://instagram.com/test_user",
                "followers": 1234,
                "bio": "Founder | Entrepreneur",
                "website": None,
                "profile_pic": None,
                "email_bio": None,
                "email_found_on_website": None,
                "email_found_linkedin": None,
                "email_guessed": None,
                "email_confidence": "low",
                "email_verified": False
            }
        ]
    }