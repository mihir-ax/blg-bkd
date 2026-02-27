"""
POST /api/v1/user/register
- Verifies the SSO JWT, creates user in InkFlow DB, returns API key
- The SSO userId (5-7 digit numeric) is the canonical link between platforms
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from jose import jwt, JWTError

from app.database import get_db
from app.config import settings
from app.utils.api_key import generate_api_key

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    display_name: Optional[str] = ""
    bio: Optional[str] = ""
    avatar_url: Optional[str] = None
    social_links: Optional[dict] = {}


def _verify_sso_jwt(token: str) -> dict:
    """Verify the JWT from svms.in SSO and return payload."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid SSO token: {str(e)}")


@router.post("/user/register")
async def register_user(
    body: RegisterRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Register a human user coming from SSO.
    Expects: Authorization: Bearer <sso_jwt>
    The JWT's 'id' field is the MongoDB _id from the SSO system.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required.")

    token = authorization.split(" ", 1)[1]
    payload = _verify_sso_jwt(token)

    # 'id' in JWT payload is the SSO MongoDB _id
    sso_user_id = payload.get("id")
    if not sso_user_id:
        raise HTTPException(status_code=401, detail="Invalid SSO token payload.")

    db = get_db()

    # Upsert: if user already exists, return their key; otherwise create
    existing = await db["users"].find_one({"sso_user_id": sso_user_id})
    if existing:
        return {
            "success": True,
            "api_key": existing["api_key"],
            "user_id": existing["sso_user_id"],
            "username": existing["username"],
            "message": "User already registered.",
        }

    # Check username uniqueness
    taken = await db["users"].find_one({"username": body.username.lower()})
    if taken:
        raise HTTPException(status_code=409, detail="Username already taken.")

    api_key = generate_api_key()
    user_doc = {
        "sso_user_id": sso_user_id,
        "username": body.username.lower(),
        "display_name": body.display_name or body.username,
        "bio": body.bio,
        "avatar_url": body.avatar_url,
        "api_key": api_key,
        "social_links": body.social_links or {},
        "created_at": datetime.utcnow(),
    }

    await db["users"].insert_one(user_doc)

    return {
        "success": True,
        "api_key": api_key,
        "user_id": sso_user_id,
        "username": body.username.lower(),
        "message": "User registered successfully.",
    }
