from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from httpx import AsyncClient


@asynccontextmanager
async def using_auth_cookie(
    client: AsyncClient, auth_cookie: str
) -> AsyncIterator[None]:
    host = getattr(getattr(client, "base_url", None), "host", None) or "testserver"
    domain = host if host.endswith(".local") else f"{host}.local"

    jar = client.cookies.jar
    previous_auth_cookies = [c for c in jar if c.name == "auth"]

    for c in previous_auth_cookies:
        try:
            jar.clear(domain=c.domain, path=c.path, name=c.name)
        except KeyError:
            pass

    client.cookies.set("auth", auth_cookie, domain=domain, path="/")
    try:
        yield
    finally:
        for c in [c for c in jar if c.name == "auth"]:
            try:
                jar.clear(domain=c.domain, path=c.path, name=c.name)
            except KeyError:
                pass

        for c in previous_auth_cookies:
            jar.set_cookie(c)
