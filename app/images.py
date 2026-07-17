import os

from dotenv import load_dotenv
from imagekitio import AsyncImageKit


load_dotenv()   # Load environment variables from the .env file

# Read the private key from the environment
private_key = os.getenv("IMAGEKIT_PRIVATE_KEY")

# Stop the application immediately if the key is missing
# This produces a clearer error than allowing ImageKit authentication to fail later

if not private_key:
    raise RuntimeError(
        "IMAGEKIT_PRIVATE_KEY is missing from the .env file"
    )

# Use the asynchronous ImageKit client becuase the FastAPI upload
# endpoint is an async function
#
# The variable is named 'imagekit' in lowercase so it matches:
# from app.images import imagekit
imagekit = AsyncImageKit(
    private_key=private_key
)

# The URL endpoint is not needed when uploading files.
# Keep it separately if you later generate transformed ImageKit URLs
IMAGEKIT_URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")