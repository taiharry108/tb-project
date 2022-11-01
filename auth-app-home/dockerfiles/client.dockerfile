FROM node:18-alpine

WORKDIR /app
COPY ./client/package.json /app
COPY ./client/tailwind.config.js /app
RUN npm i
