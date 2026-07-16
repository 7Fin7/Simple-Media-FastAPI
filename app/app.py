from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate, PostResponse
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
     await create_db_and_tables()
     yield

app = FastAPI(lifespan=lifespan)

text_posts = {
    1: {"title": "Getting Started with FastAPI", "content": "This is my first post while learning how to build APIs with FastAPI."},
    2: {"title": "Understanding API Routes", "content": "Routes determine which function runs when a user visits a specific API endpoint."},
    3: {"title": "Using Path Parameters", "content": "Path parameters allow an API endpoint to accept values directly from the URL."},
    4: {"title": "Working with Query Parameters", "content": "Query parameters can be used to filter or customise the data returned by an API."},
    5: {"title": "Creating a New Post", "content": "FastAPI makes it simple to receive JSON data and create new resources."},
    6: {"title": "Updating Existing Data", "content": "PUT and PATCH requests can be used to update existing posts."},
    7: {"title": "Deleting a Post", "content": "DELETE requests allow users to remove resources from the application."},
    8: {"title": "Using Pydantic Models", "content": "Pydantic models validate incoming data and ensure it follows the expected structure."},
    9: {"title": "FastAPI Automatic Documentation", "content": "FastAPI automatically generates interactive API documentation using Swagger UI."},
    10: {"title": "Next Steps", "content": "The next stage of this project is connecting the FastAPI application to a database."}
}

# All posts
@app.get("/posts")
def get_all_posts(limit: int = None):
    if limit:
         return list(text_posts.values())[:limit]
    
    return text_posts

# Single post with path parameter
@app.get("/posts/{id}")
def get_post(id: int) -> PostResponse:
    if id not in text_posts:
            raise HTTPException(status_code=404, detail="Post not found")
    
    return text_posts.get(id)

# Post post
@app.post("/posts")
def create_post(post: PostCreate) -> PostResponse:
    new_post = {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post
    return new_post

