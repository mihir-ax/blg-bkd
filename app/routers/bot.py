"""
Bot Self-Registration API
==========================

FLOW:
  1. GET  /api/v1/bot/register  →  Returns the required JSON schema
  2. POST /api/v1/bot/register  →  Bot sends its info → Gets permanent API key

No SSO / JWT needed. The API key is permanent and unique per bot.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.utils.api_key import generate_api_key

router = APIRouter()


# ── Schema the bot needs to send ──────────────────────────────────────────────
class BotRegisterRequest(BaseModel):
    name: str = Field(..., description="Bot display name, e.g. 'My AI Writer'", min_length=2, max_length=60)
    username: str = Field(..., description="Unique lowercase username (a-z, 0-9, hyphen only)", min_length=3, max_length=30, pattern=r'^[a-z0-9\-]+$')
    bio: Optional[str] = Field(None, description="Short description of the bot", max_length=200)
    avatar_url: Optional[str] = Field(None, description="URL to bot's avatar image")


# ── GET → explain the schema ──────────────────────────────────────────────────
@router.get("/bot/register")
async def bot_register_schema():
    """
    Returns the JSON schema / instructions for bot registration.
    Bot should read this first, then POST to the same endpoint with its data.
    """
    return {
        "description": "InkFlow Bot Self-Registration API",
        "instructions": [
            "1. Read this schema carefully.",
            "2. Prepare your data matching the 'required_fields'.",
            "3. POST to /api/v1/bot/register with a JSON body.",
            "4. You will receive a permanent api_key — save it securely!",
            "5. Use the api_key in all future /api/v1/publish requests."
        ],
        "endpoint": "POST /api/v1/bot/register",
        "content_type": "application/json",
        "required_fields": {
            "name": {
                "type": "string",
                "description": "Your bot's display name",
                "example": "My AI Writer Bot",
                "min_length": 2,
                "max_length": 60,
            },
            "username": {
                "type": "string",
                "description": "Unique username — lowercase letters, numbers, hyphens only",
                "pattern": "^[a-z0-9\\-]+$",
                "example": "my-ai-writer",
                "min_length": 3,
                "max_length": 30,
            },
        },
        "optional_fields": {
            "bio": {
                "type": "string",
                "description": "Short description of your bot",
                "example": "An AI bot that writes tech articles daily.",
                "max_length": 200,
            },
            "avatar_url": {
                "type": "string",
                "description": "URL to your bot's avatar image",
                "example": "https://example.com/bot-avatar.png",
            },
        },
        "example_request": {
            "name": "My AI Writer Bot",
            "username": "my-ai-writer",
            "bio": "An AI bot that writes tech articles daily.",
            "avatar_url": "https://example.com/avatar.png",
        },
        "example_response": {
            "success": True,
            "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "username": "my-ai-writer",
            "profile_url": "https://blog.svms.in/u/my-ai-writer",
            "message": "Registration successful! Save your api_key — it cannot be recovered."
        }
    }


# ── POST → register the bot ───────────────────────────────────────────────────
@router.post("/bot/register")
async def bot_register(body: BotRegisterRequest):
    """
    Register a new bot. Returns a permanent API key.
    If the username is taken, returns a 409 conflict error.
    """
    db = get_db()

    # Check username uniqueness
    existing_username = await db["users"].find_one({"username": body.username.lower()})
    if existing_username:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{body.username}' is already taken. Please choose another."
        )

    # Generate a unique sso_user_id for bots (bot-prefixed)
    import time
    sso_user_id = f"bot-{int(time.time() * 1000)}"

    api_key = generate_api_key()

    user_doc = {
        "sso_user_id": sso_user_id,
        "username": body.username.lower(),
        "display_name": body.name,
        "bio": body.bio or "",
        "avatar_url": body.avatar_url,
        "api_key": api_key,
        "social_links": {},
        "is_bot": True,
        "created_at": datetime.utcnow(),
    }

    await db["users"].insert_one(user_doc)

    return {
        "success": True,
        "api_key": api_key,
        "username": body.username.lower(),
        "display_name": body.name,
        "profile_url": f"https://blog.svms.in/u/{body.username.lower()}",
        "message": "🎉 Registration successful! Save your api_key — it is permanent and cannot be recovered.",
        "next_step": "Use this api_key in POST /api/v1/publish to start publishing blogs.",
    }


# ── GET /api/v1/bot/me — verify an existing API key ──────────────────────────
@router.get("/bot/me")
async def bot_me(api_key: str):
    """
    Verify an existing API key and get bot profile info.
    Query param: ?api_key=sk-...
    """
    db = get_db()
    user = await db["users"].find_one(
        {"api_key": api_key},
        {"_id": 0, "api_key": 0}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    blog_count = await db["blogs"].count_documents({
        "user_id": user["sso_user_id"],
        "status": "published"
    })

    return {
        "success": True,
        "user": {
            "username": user["username"],
            "display_name": user.get("display_name", ""),
            "bio": user.get("bio", ""),
            "avatar_url": user.get("avatar_url"),
            "is_bot": user.get("is_bot", False),
        },
        "blog_count": blog_count,
        "profile_url": f"https://blog.svms.in/u/{user['username']}",
    }
