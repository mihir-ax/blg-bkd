from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import connect_db, close_db, get_db
from app.config import settings
from app.routers import auth, publish, blogs, users, feed, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    db = get_db()
    # Create MongoDB indexes on startup
    await db["blogs"].create_index([
        ("title", "text"),
        ("description", "text"),
        ("content", "text"),
        ("tags", "text"),
    ])
    await db["blogs"].create_index("slug", unique=True)
    await db["blogs"].create_index("user_id")
    await db["blogs"].create_index("status")
    await db["users"].create_index("api_key", unique=True)
    await db["users"].create_index("username", unique=True)
    await db["users"].create_index("sso_user_id", unique=True)
    print("✅ Indexes created")
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="InkFlow API",
    description="API-first blogging platform for AI agents and humans",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "https://accounts.svms.in", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(publish.router, prefix="/api/v1", tags=["Publish"])
app.include_router(blogs.router, prefix="/api/v1", tags=["Blogs"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(feed.router, prefix="/api/v1", tags=["Feed"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])


@app.get("/")
async def root():
    return {
        "name": "InkFlow API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running 🚀",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
