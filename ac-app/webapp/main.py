"""Application module."""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from boostrap import bootstrap_di

bootstrap_di()

from container import Container
from routers import api, main, auth, user


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

    app.mount("/css", StaticFiles(directory="/client/src/css/"), name="css")
    app.mount("/scripts", StaticFiles(directory="/client/src/scripts/"), name="css")

    # setattr(app, "container", container)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="/auth")
    app.include_router(user.router, prefix="/user")
    app.include_router(main.router, prefix="")
    container.init_resources()

    return app


app = create_app()


@app.on_event("shutdown")
async def on_shutdown():
    getattr(app, "container").shutdown_resources()
