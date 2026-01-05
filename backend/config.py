from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from starlette.config import Config
from starlette.datastructures import Secret

config = Config("backend/.env")


def add_sql_driver(url: str):
    if not url.startswith("postgres"):
        return url

    parsed = urlparse(url)
    return urlunparse(parsed._replace(scheme="postgresql+psycopg"))


def add_ssl_none(url: str):
    if url.startswith("redis://"):
        return url

    parsed = urlparse(url)

    path = "/"
    params = dict(parse_qsl(parsed.query))
    params["ssl_cert_reqs"] = "none"

    new_query = urlencode(params)

    return urlunparse(parsed._replace(path=path, query=new_query))


DATABASE_URL = add_sql_driver(
    config("DATABASE_URL", default="sqlite+aiosqlite:///minesweeper.db")
)
REDIS_URL = add_ssl_none(config("REDIS_URL", default="redis://localhost:6379"))

AUTH_SECRET = config("AUTH_SECRET", cast=Secret, default="RePeEwSeNiM")

FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = config("BACKEND_URL", default="http://localhost:8000/api")

AWS_ACCESS_KEY_ID = config("BUCKETEER_AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = config(
    "BUCKETEER_AWS_SECRET_ACCESS_KEY", cast=Secret, default=None
)
AWS_REGION = config("BUCKETEER_AWS_REGION", default=None)
AWS_BUCKET_NAME = config("BUCKETEER_BUCKET_NAME", default=None)
DEV = "localhost" in BACKEND_URL
