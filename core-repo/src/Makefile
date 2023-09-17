.PHONY: migrate



migrate:
	@alembic revision --autogenerate -m ${MIGRATION_MESSAGE} && alembic upgrade head
