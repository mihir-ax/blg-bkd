"""
POST /api/v1/publish  — Publish or update a blog post
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from app.database import get_db
from app.models.blog import PublishRequest
from app.utils.slug import make_slug, unique_slug
from app.utils.seo import auto_description, auto_reading_time
from app.config import settings

router = APIRouter()


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def _get_user_by_api_key(api_key: str, db):
    user = await db["users"].find_one({"api_key": api_key})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return user


@router.post("/publish")
async def publish_blog(body: PublishRequest):
    db = get_db()

    # 1. Authenticate via API key — fetch user from DB
    user = await _get_user_by_api_key(body.api_key, db)
    blog = body.blog

    # 2. Resolve slug
    base_slug = make_slug(blog.slug or blog.title)
    final_slug = await unique_slug(base_slug, db)

    # 3. Auto-fill missing optional fields
    description = blog.description or auto_description(blog.content)
    reading_time = blog.reading_time_minutes or auto_reading_time(blog.content)

    # 4. Build SEO meta dict
    seo_meta = {}
    if blog.seo:
        seo_meta = blog.seo.model_dump(exclude_none=True)
    if "meta_title" not in seo_meta:
        seo_meta["meta_title"] = blog.title
    if "meta_description" not in seo_meta:
        seo_meta["meta_description"] = description

    # 5. Check if this is an UPDATE (same title + same user)
    existing = await db["blogs"].find_one({
        "user_id": user["sso_user_id"],
        "slug": base_slug,   # original slug before collision fallback
    })

    now = datetime.utcnow()

    if existing:
        # Update existing blog
        await db["blogs"].update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "title": blog.title,
                "description": description,
                "content": blog.content,
                "content_format": blog.content_format or "markdown",
                "cover_image_url": blog.cover_image_url,
                "tags": [t.lower() for t in blog.tags],
                "category": blog.category or "General",
                "language": blog.language or "en",
                "reading_time": reading_time,
                "seo_meta": seo_meta,
                "updated_at": now,
            }}
        )
        blog_id = str(existing["_id"])
        slug = existing["slug"]
    else:
        # Insert new blog
        blog_doc = {
            "user_id": user["sso_user_id"],
            "title": blog.title,
            "slug": final_slug,
            "description": description,
            "content": blog.content,
            "content_format": blog.content_format or "markdown",
            "cover_image_url": blog.cover_image_url,
            "tags": [t.lower() for t in blog.tags],
            "category": blog.category or "General",
            "language": blog.language or "en",
            "reading_time": reading_time,
            "status": "published",
            "view_count": 0,
            "seo_meta": seo_meta,
            "published_at": now,
            "created_at": now,
            "updated_at": now,
        }
        result = await db["blogs"].insert_one(blog_doc)
        blog_id = str(result.inserted_id)
        slug = final_slug

    blog_url = f"{settings.frontend_url}/blog/{slug}"

    return {
        "success": True,
        "blog_url": blog_url,
        "blog_id": blog_id,
        "user_id": user["sso_user_id"],
        "slug": slug,
        "published_at": now.isoformat(),
    }
