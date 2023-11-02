# Manga viewer FastAPI application with a SSO authentication application
## Documentated Applications
### AC App
It is a web application that allows you to read manga and watch anime from scraping different websites. You can create more scraping service under `ac-app/webapp/core/scraping_service`.
### Auth App
It is the centralized authentcation application.
## Getting Started
### Prerequisites
All applications are containerized so you just need docker to get everything running! My docker version is `24.0.5`.
### Environment Setup
1. Create a `.env` in the root directory with these two vairables `POSTGRES_PASSWORD` and `POSTGRES_USER`.
2. Run `setup-env.sh`. It generates private and public keys for JWT, creates docker network interface and other necessarily config files.
### Running app servers
Start the application servers
```
make run COMPOSE_FILE=./ac-app/docker-compose.yml
make run COMPOSE_FILE=./auth-app/docker-compose.yml
make run COMPOSE_FILE=./core-repo/docker-compose.yml
```
Note: `core-repo` should be run at last. It creates a postgres, redis, and nginx server, which acts as a reverse proxy server.
Now you should be able to access the AC app by 
`
http://localhost/ac/
`
, which should prompt you to sign in. 
