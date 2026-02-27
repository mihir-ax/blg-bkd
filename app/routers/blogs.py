"""
GET  /api/v1/blog/{slug}    → Get full blog post by slug
DELETE /api/v1/blog/{slug}  → Delete blog (API Key auth)
"""
from fastapi import APIRouter, HTTPException, Header
from bson import ObjectId
from typing import Optional
from datetime import datetime

from app.database import get_db

router = APIRouter()


def _doc_to_dict(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def _get_user_by_api_key(api_key: str, db):
    user = await db["users"].find_one({"api_key": api_key})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return user


@router.get("/blog/{slug}")
async def get_blog(slug: str):
    db = get_db()
    blog = await db["blogs"].find_one({"slug": slug, "status": "published"})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found.")

    # Increment view count (fire and forget style)
    await db["blogs"].update_one({"_id": blog["_id"]}, {"$inc": {"view_count": 1}})
    blog["view_count"] += 1

    blog = _doc_to_dict(blog)

    # Attach author info
    author = await db["users"].find_one(
        {"sso_user_id": blog["user_id"]},
        {"_id": 0, "api_key": 0}
    )
    blog["author"] = author

    return {"success": True, "blog": blog}


@router.delete("/blog/{slug}")
async def delete_blog(
    slug: str,
    x_api_key: Optional[str] = Header(None)
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required.")

    db = get_db()
    user = await _get_user_by_api_key(x_api_key, db)

    blog = await db["blogs"].find_one({"slug": slug})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found.")

    if blog["user_id"] != user["sso_user_id"]:
        raise HTTPException(status_code=403, detail="You don't own this blog.")

    await db["blogs"].delete_one({"_id": blog["_id"]})
    return {"success": True, "message": f"Blog '{slug}' deleted."}
