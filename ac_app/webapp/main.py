"""Application module."""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from container import Container
from routers import api


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setattr(app, 'container', container)
    app.include_router(api.router, prefix="/api")
    container.init_resources()

    return app


app = create_app()


@app.on_event("shutdown")
async def on_shutdown():
    getattr(app, "container").shutdown_resources()
