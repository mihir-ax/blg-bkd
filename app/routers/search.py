"""
GET /api/v1/search  → Full-text search across title, description, tags, content
"""
from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_db

router = APIRouter()


@router.get("/search")
async def search_blogs(
    q: str = Query(..., min_length=1),
    tag: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
):
    db = get_db()

    # MongoDB $text full-text search (needs text index)
    query: dict = {
        "$text": {"$search": q},
        "status": "published",
    }

    if tag:
        query["tags"] = tag.lower()
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if language:
        query["language"] = language
    if author:
        # Look up user_id by username first
        user = await db["users"].find_one({"username": author.lower()}, {"sso_user_id": 1})
        if user:
            query["user_id"] = user["sso_user_id"]
        else:
            return {"success": True, "results": [], "total": 0}

    skip = (page - 1) * limit
    projection = {"content": 0, "score": {"$meta": "textScore"}}
    cursor = (
        db["blogs"]
        .find(query, projection)
        .sort([("score", {"$meta": "textScore"})])
        .skip(skip)
        .limit(limit)
    )

    results = []
    async for doc in cursor:
        doc.pop("score", None)
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)

    total = await db["blogs"].count_documents(query)

    # Attach author info
    user_ids = list({r["user_id"] for r in results})
    authors_cursor = db["users"].find(
        {"sso_user_id": {"$in": user_ids}},
        {"sso_user_id": 1, "username": 1, "display_name": 1, "avatar_url": 1}
    )
    authors = {}
    async for a in authors_cursor:
        a.pop("_id", None)
        authors[a["sso_user_id"]] = a
    for r in results:
        r["author"] = authors.get(r["user_id"], {})

    return {
        "success": True,
        "results": results,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }
