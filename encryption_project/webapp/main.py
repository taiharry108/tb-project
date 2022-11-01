"""Application module."""


from fastapi import FastAPI
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from container import Container

from routers import encryption, auth, main, admin


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
    container.init_resources()

    app.mount("/static", StaticFiles(directory="/client/src/scripts"), name="static")
    app.mount("/css", StaticFiles(directory="/client/src/css/"), name="css")

    app.include_router(encryption.router, prefix="/api")
    app.include_router(auth.router, prefix="/auth")
    app.include_router(main.router, prefix="")
    app.include_router(admin.router, prefix="/admin")

    return app


app = create_app()


@app.on_event("shutdown")
async def on_shutdown():
    getattr(app, "container").shutdown_resources()
