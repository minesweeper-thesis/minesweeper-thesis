from starlette.config import Config
from starlette.datastructures import Secret

config = Config("backend/.env")

DATABASE_URL = config("DATABASE_URL", default="sqlite+aiosqlite:///minesweeper.db")
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379")

AUTH_SECRET = config("AUTH_SECRET", cast=Secret, default="RePeEwSeNiM")

FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = config("BACKEND_URL", default="http://localhost:8000/api")

AWS_ACCESS_KEY_ID = config("BUCKETEER_AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = config(
    "BUCKETEER_AWS_SECRET_ACCESS_KEY", cast=Secret, default=None
)
AWS_REGION = config("BUCKETEER_AWS_REGION", default=None)
AWS_BUCKET_NAME = config("BUCKETEER_BUCKET_NAME", default=None)
