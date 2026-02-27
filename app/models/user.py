from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class User(BaseModel):
    sso_user_id: str           # 5-7 digit numeric ID from svms.in SSO
    username: str
    display_name: Optional[str] = ""
    bio: Optional[str] = ""
    avatar_url: Optional[str] = None
    api_key: str               # sk-xxxx
    social_links: Optional[Dict[str, str]] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserPublic(BaseModel):
    sso_user_id: str
    username: str
    display_name: Optional[str] = ""
    bio: Optional[str] = ""
    avatar_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = {}
    created_at: datetime
