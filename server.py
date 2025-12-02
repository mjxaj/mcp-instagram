from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instagrapi import Client
from dotenv import load_dotenv
from fastapi.concurrency import run_in_threadpool
import uvicorn
import os
import re
import requests
from urllib.parse import urlparse

def extract_emails_from_text(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text) if text else []

def extract_emails_from_website(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=5)
        emails_on_page = extract_emails_from_text(r.text)
        return emails_on_page[0] if emails_on_page else None
    except:
        return None

def guess_email(username, fullname, domain="gmail.com"):
    if not username:
        return None
    username_clean = re.sub(r'\W+', '', username.lower())
    guessed = f"{username_clean}@{domain}"
    return guessed

def email_confidence_level(email_bio, email_site, email_linkedin, email_guess):
    if email_bio:
        return "high"
    if email_site or email_linkedin:
        return "medium"
    if email_guess:
        return "low"
    return "low"

def email_verified_check(email_bio, email_site):
    return email_bio is not None or email_site is not None

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_PROXY = os.getenv("IG_PROXY")
DEFAULT_PORT = 3001
PORT = int(os.environ["PORT"]) if "PORT" in os.environ else DEFAULT_PORT

app = FastAPI()
client = Client()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if IG_PROXY:
    client.set_proxy(IG_PROXY)

@app.on_event("startup")
def startup_event():
    try:
        client.login(IG_USERNAME, IG_PASSWORD)
        print(f"Logged in as {IG_USERNAME}")
    except Exception as e:
        print("Login failed:", str(e))

class FounderSearchInput(BaseModel):
    query: str
    limit: int = 20

FOUNDER_KEYWORDS = [
    "founder", "cofounder", "co-founder", "ceo", "owner", "director",
    "agency", "brand", "startup", "entrepreneur", "business"
]

@app.get("/.well-known/mcp.json")
def serve_mcp():
    return FileResponse(".well-known/mcp.json", media_type="application/json")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/instagram_search_founders")
async def instagram_search_founders(input: FounderSearchInput):
    try:
        raw_results = await run_in_threadpool(client.search_users, input.query)
        results = raw_results[:input.limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    output = []
    for user in results:
        try:
            info = await run_in_threadpool(client.user_info, user.pk)
        except:
            continue

        bio = info.biography or ""
        if not any(k.lower() in bio.lower() for k in FOUNDER_KEYWORDS):
            continue

        email_bio = (extract_emails_from_text(info.biography) or [None])[0]
        email_site = extract_emails_from_website(info.external_url)
        email_linkedin = extract_emails_from_website(info.external_url) if info.external_url and "linkedin" in info.external_url.lower() else None
        domain = (urlparse(info.external_url).netloc.replace("www.", "") if info.external_url else "gmail.com") or "gmail.com"
        email_guess = guess_email(info.username, info.full_name, domain)
        confidence = email_confidence_level(email_bio, email_site, email_linkedin, email_guess)
        email_verified = email_verified_check(email_bio, email_site)

        output.append({
            "username": info.username,
            "full_name": info.full_name,
            "instagram": f"https://instagram.com/{info.username}",
            "followers": info.follower_count,
            "bio": info.biography,
            "website": info.external_url,
            "profile_pic": str(info.profile_pic_url),
            "email_bio": email_bio,
            "email_found_on_website": email_site,
            "email_found_linkedin": email_linkedin,
            "email_guessed": email_guess,
            "email_confidence": confidence,
            "email_verified": email_verified
        })

    return {"results": output}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
