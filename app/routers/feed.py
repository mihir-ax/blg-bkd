"""
GET /api/v1/feed  → Cursor-based paginated global latest blogs
"""
from fastapi import APIRouter, Query
from typing import Optional
from bson import ObjectId
from app.database import get_db

router = APIRouter()


@router.get("/feed")
async def get_feed(
    limit: int = Query(12, le=50),
    cursor: Optional[str] = Query(None, description="Last blog _id for pagination"),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
):
    db = get_db()

    query: dict = {"status": "published"}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if language:
        query["language"] = language
    if cursor:
        try:
            query["_id"] = {"$lt": ObjectId(cursor)}
        except Exception:
            pass

    cursor_obj = db["blogs"].find(query, {"content": 0}).sort("_id", -1).limit(limit)

    blogs = []
    last_id = None
    async for doc in cursor_obj:
        last_id = str(doc["_id"])
        doc["id"] = str(doc.pop("_id"))
        blogs.append(doc)

    # Attach author usernames in bulk
    user_ids = list({b["user_id"] for b in blogs})
    authors_cursor = db["users"].find(
        {"sso_user_id": {"$in": user_ids}},
        {"sso_user_id": 1, "username": 1, "display_name": 1, "avatar_url": 1}
    )
    authors = {}
    async for a in authors_cursor:
        a.pop("_id", None)
        authors[a["sso_user_id"]] = a

    for b in blogs:
        b["author"] = authors.get(b["user_id"], {})

    return {
        "success": True,
        "blogs": blogs,
        "next_cursor": last_id if len(blogs) == limit else None,
    }
