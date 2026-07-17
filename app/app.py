from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate, PostResponse
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
from pathlib import Path
import shutil
import os
import uuid
import tempfile


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None

    try:
        # UploadFile.filename can technically be None,
        # so check that a filename was supplied
        if not file.filename:
            raise HTTPException(
                status_code = 400,
                detail = "The uploaded file must have a filename",
            )
        
        # Get the original extension, such as .jpg or .mp4
        file_extension = os.path.splitext(file.filename)[1]

        # Create a temporary file on the server
        #
        # delete = False is needed becuase ImageKit must be able to
        # access the file after the block finishes
        with tempfile.NamedTemporaryFile(
            delete = False,
            suffix = file_extension,
        ) as temp_file:
            temp_file_path = temp_file.name

            # Copy the uploaded file into the temporary file
            shutil.copyfileobj(file.file, temp_file)

        # Upload the temporary file to ImageKit
        #
        # The current SDK uses imagekit.files.upload()
        # Because imagekit is an AsyncImageKit client, it must be awaited

        upload_result = await imagekit.files.upload(
            file = Path(temp_file_path),
            file_name = file.filename,
            use_unique_file_name=True,
            tags = ["backend-upload"],
        )

        # Work out whetehr the uploaded file is a video or an image
        content_type = file.content_type or ""

        if content_type.startswith("video/"):
            file_type = "video"
        elif content_type.startswith("image/"):
            file_type = "image"
        else:
            raise HTTPException(
                status_code = 400,
                detail = "Omly image and video files are supported",
            )

        # Create a new SQLAlchemy Post object
        post = Post(
            caption = caption,
            url = upload_result.url,
            file_type = file_type,
            file_name = upload_result.name,
        )


        # Add the object to the current database session
        session.add(post)

        # Save the new post the database
        await session.commit()

        # Reload the objet so generated fields such as the ID
        # and creation date are available
        await session.refresh(post)

        return {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
        }
    
    except HTTPException:
        # Allow intentional HTTP errors, such as 400 responses,
        # to pass through unchanged
        raise

    except Exception as error:
        # Unexpected errors become 500 responses
        raise HTTPException(
            status_code = 500,
            detail = str(error),
        ) from error
    
    finally:
        # Delete the temporary file whethe the upload suceeds or fails
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        # Close teh FastAPI UploadFile
        await file.close()

@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat()
            }
        )

    return {"posts": posts_data}