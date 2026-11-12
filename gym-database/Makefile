.DEFAULT_GOAL := help
COMPOSE := docker compose
.PHONY: help up db migrate seed status rollback verify down logs psql
help:
	@echo 'up       Start PostgreSQL and apply schema migrations'
	@echo 'seed     Apply schema and insert optional demo data'
	@echo 'status   List applied/pending migrations'
	@echo 'verify   Check constraints in a rolled-back transaction'
	@echo 'rollback Undo the latest migration (deletes its data)'
	@echo 'down     Stop containers; preserve database volume'
	@echo 'psql     Open PostgreSQL console'
db:
	$(COMPOSE) up -d --wait db
up: migrate
migrate: db
	$(COMPOSE) run --rm --build migrate up
seed: migrate
	$(COMPOSE) run --rm --build migrate seed
status: db
	$(COMPOSE) run --rm --build migrate status
rollback: db
	$(COMPOSE) run --rm --build migrate down
verify: migrate
	$(COMPOSE) run --rm --build --entrypoint python migrate scripts/verify.py
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs -f db
psql:
	$(COMPOSE) exec db psql -U gym_user -d gym
