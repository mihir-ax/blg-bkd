from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SeoMeta(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image: Optional[str] = None
    canonical_url: Optional[str] = None
    focus_keyword: Optional[str] = None
    schema_type: Optional[str] = "Article"


class BlogSEOInput(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image: Optional[str] = None
    canonical_url: Optional[str] = None
    focus_keyword: Optional[str] = None
    schema_type: Optional[str] = "Article"


class BlogInput(BaseModel):
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    content: str
    content_format: Optional[str] = "markdown"
    cover_image_url: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = "General"
    language: Optional[str] = "en"
    reading_time_minutes: Optional[int] = None
    seo: Optional[BlogSEOInput] = None


class PublishRequest(BaseModel):
    api_key: str
    blog: BlogInput


class Blog(BaseModel):
    id: Optional[str] = None
    user_id: str                   # sso_user_id
    title: str
    slug: str
    description: str
    content: str
    content_format: str = "markdown"
    cover_image_url: Optional[str] = None
    tags: List[str] = []
    category: str = "General"
    language: str = "en"
    reading_time: int = 1
    status: str = "published"
    view_count: int = 0
    seo_meta: Optional[Dict[str, Any]] = {}
    published_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BlogPublic(BaseModel):
    id: str
    user_id: str
    title: str
    slug: str
    description: str
    cover_image_url: Optional[str] = None
    tags: List[str] = []
    category: str
    language: str
    reading_time: int
    view_count: int
    seo_meta: Optional[Dict[str, Any]] = {}
    published_at: datetime
    author: Optional[Dict[str, Any]] = None  # populated on fetch
