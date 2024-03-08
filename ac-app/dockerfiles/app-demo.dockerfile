FROM python:3.11-alpine

# set working directory
WORKDIR /webapp

# set environment varibles
# prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apk --update --no-cache add gcc make g++ zlib-dev libffi-dev openvpn

# install python dependencies
RUN pip install --upgrade pip
COPY ./ac-app/requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./core-repo/async_service/ /core/async_service
COPY ./core-repo/database/ /core/database
COPY ./core-repo/download_service/ /core/download_service
COPY ./core-repo/queue_service/ /core/queue_service
COPY ./core-repo/secret_service/ /core/secret_service
COPY ./core-repo/security_service/ /core/security_service
COPY ./core-repo/session/ /core/session
COPY ./core-repo/store_service/ /core/store_service
COPY ./ac-app/client /client

# add app
COPY ./ac-app/webapp /webapp

ENV PYTHONPATH=/core

EXPOSE 8000

ENTRYPOINT [ "uvicorn", "main:app", "--host", "0.0.0.0"]
