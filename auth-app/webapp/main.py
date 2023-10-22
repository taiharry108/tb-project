"""Application module."""
from contextlib import asynccontextmanager
from logging import config
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from boostrap import bootstrap_di

bootstrap_di()

from routers import main


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.fileConfig("logging.conf", disable_existing_loggers=False)
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    origins = ["http://localhost:60889"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/css", StaticFiles(directory="/client/src/css/"), name="css")
    app.include_router(main.router, prefix="/user")

    return app


app = create_app()


# @app.get("/")
# async def root():
#     return {"message": "hello world!"}
