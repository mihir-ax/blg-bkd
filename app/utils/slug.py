import re
from slugify import slugify as python_slugify


def make_slug(text: str) -> str:
    """Convert text to a URL-safe lowercase slug."""
    return python_slugify(text, max_length=80, word_boundary=True)


async def unique_slug(base_slug: str, db, blog_id: str = None) -> str:
    """
    Ensure slug is unique in the blogs collection.
    Appends -2, -3, ... on collision.
    If blog_id is provided, ignore that document (edit case).
    """
    slug = base_slug
    counter = 2
    while True:
        query = {"slug": slug}
        if blog_id:
            query["_id"] = {"$ne": blog_id}
        existing = await db["blogs"].find_one(query, {"_id": 1})
        if not existing:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
