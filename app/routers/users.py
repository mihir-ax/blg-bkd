"""
GET /api/v1/user/{username} → User profile + their published blogs
"""
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db

router = APIRouter()


@router.get("/user/{username}")
async def get_user(username: str, page: int = Query(1, ge=1), limit: int = Query(10, le=50)):
    db = get_db()
    user = await db["users"].find_one(
        {"username": username.lower()},
        {"_id": 0, "api_key": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    skip = (page - 1) * limit
    cursor = db["blogs"].find(
        {"user_id": user["sso_user_id"], "status": "published"},
        {"content": 0}          # Exclude heavy content field from listing
    ).sort("published_at", -1).skip(skip).limit(limit)

    blogs = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        blogs.append(doc)

    total = await db["blogs"].count_documents({"user_id": user["sso_user_id"], "status": "published"})

    return {
        "success": True,
        "user": user,
        "blogs": blogs,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }
