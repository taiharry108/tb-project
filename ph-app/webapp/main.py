"""Application module."""


from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from container import Container
from routers import api, main


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        # allow_origins=["http://tai-server.local:60890"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setattr(app, "container", container)
    app.include_router(api.router, prefix="/api")
    app.include_router(main.router, prefix="")
    container.init_resources()

    return app


app = create_app()


@app.on_event("shutdown")
async def on_shutdown():
    getattr(app, "container").shutdown_resources()


@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
