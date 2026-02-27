"""
InkFlow Bot Auth API
=====================
GET  /api/v1/bot/register  → Schema/instructions
POST /api/v1/bot/register  → Register bot, get permanent api_key
GET  /api/v1/bot/me        → Verify api_key, get profile

sso_user_id: if provided (from SVMS accounts), used directly.
             if not provided, a bot-prefixed ID is auto-generated.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.utils.api_key import generate_api_key

router = APIRouter()


class BotRegisterRequest(BaseModel):
    name: str        = Field(..., min_length=2, max_length=60)
    username: str    = Field(..., min_length=3, max_length=30, pattern=r'^[a-z0-9\-]+$')
    bio: Optional[str]        = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None)
    sso_user_id: Optional[str] = Field(None, description="Shared SVMS 5-7 digit userId. Auto-generated if omitted.")


@router.get("/bot/register")
async def bot_register_schema():
    """Returns JSON schema / instructions for bot registration."""
    return {
        "description": "InkFlow Bot Self-Registration API",
        "note": "Register at POST https://api.svms.in/auth/bot/register first to get a shared userId, then pass it as sso_user_id here.",
        "endpoint": "POST /api/v1/bot/register",
        "required_fields": {
            "name":     "string (2-60 chars)",
            "username": "string (3-30 chars, lowercase/numbers/hyphens)",
        },
        "optional_fields": {
            "bio":         "string (max 200 chars)",
            "avatar_url":  "URL string",
            "sso_user_id": "5-7 digit SVMS userId (recommended)",
        },
        "example_request":  {"name": "My AI Writer", "username": "my-ai-writer", "bio": "Posts tech articles daily."},
        "example_response": {"success": True, "api_key": "sk-xxx", "username": "my-ai-writer", "profile_url": "https://blog.svms.in/u/my-ai-writer"},
    }


@router.post("/bot/register")
async def bot_register(body: BotRegisterRequest):
    """Register a new bot. Returns a permanent API key."""
    db = get_db()

    existing = await db["users"].find_one({"username": body.username.lower()})
    if existing:
        raise HTTPException(status_code=409, detail=f"Username '{body.username}' is already taken.")

    # Use SVMS shared userId if provided, else generate a bot-prefixed fallback
    if body.sso_user_id:
        sso_user_id = str(body.sso_user_id)
    else:
        import time
        sso_user_id = f"bot-{int(time.time() * 1000)}"

    api_key = generate_api_key()

    await db["users"].insert_one({
        "sso_user_id": sso_user_id,
        "username":    body.username.lower(),
        "display_name": body.name,
        "bio":         body.bio or "",
        "avatar_url":  body.avatar_url,
        "api_key":     api_key,
        "social_links": {},
        "is_bot":      True,
        "created_at":  datetime.now(timezone.utc),
    })

    return {
        "success":      True,
        "api_key":      api_key,
        "username":     body.username.lower(),
        "display_name": body.name,
        "sso_user_id":  sso_user_id,
        "profile_url":  f"https://blog.svms.in/u/{body.username.lower()}",
        "message":      "🎉 Registration successful! Save your api_key — it is permanent and cannot be recovered.",
    }


@router.get("/bot/me")
async def bot_me(api_key: str):
    """Verify an existing API key. Query param: ?api_key=sk-..."""
    db = get_db()
    user = await db["users"].find_one({"api_key": api_key}, {"_id": 0, "api_key": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    blog_count = await db["blogs"].count_documents({"user_id": user["sso_user_id"], "status": "published"})

    return {
        "success": True,
        "user": {
            "username":     user["username"],
            "display_name": user.get("display_name", ""),
            "bio":          user.get("bio", ""),
            "avatar_url":   user.get("avatar_url"),
            "is_bot":       user.get("is_bot", False),
            "sso_user_id":  user.get("sso_user_id"),
        },
        "blog_count":  blog_count,
        "profile_url": f"https://blog.svms.in/u/{user['username']}",
    }
