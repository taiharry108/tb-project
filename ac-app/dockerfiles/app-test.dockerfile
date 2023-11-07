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
COPY test-requirements.txt .
RUN pip install --no-cache-dir --upgrade -r test-requirements.txt

# add app
COPY ./webapp /webapp
