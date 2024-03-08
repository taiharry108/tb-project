FROM python:3.11-alpine

# set working directory
WORKDIR /webapp

# set environment varibles
# prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apk --update add gcc make g++ zlib-dev libffi-dev

# install python dependencies
RUN pip install --upgrade pip
COPY ./auth-app/requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./auth-app/webapp /webapp/
COPY ./core-repo/database/ /core/database
COPY ./core-repo/session/ /core/session
COPY ./core-repo/secret_service/ /core/secret_service
COPY ./auth-app/client /client

ENV PYTHONPATH=/core

EXPOSE 8000

ENTRYPOINT [ "uvicorn", "main:app", "--host", "0.0.0.0"]
