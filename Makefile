.PHONY: up down build logs test seed-admin seed-data init-minio frontend-dev admin-dev lint clean

# Development
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

restart:
	docker compose restart

# Database
migrate:
	docker compose exec backend alembic upgrade head

migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# Seeds
seed-admin:
	docker compose exec backend python scripts/seed_admin.py

seed-data:
	docker compose exec backend python scripts/seed_sample_data.py

init-minio:
	docker compose exec backend python scripts/init_minio_buckets.py

# Testing
test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

test-frontend:
	cd frontend && npm run test

test-admin:
	cd frontend-admin && npm run test

test-all:
	bash scripts/run_all_tests.sh

# Frontend dev (outside docker)
frontend-dev:
	cd frontend && npm run dev

admin-dev:
	cd frontend-admin && npm run dev

# Lint
lint:
	cd frontend && npm run lint
	cd frontend-admin && npm run lint

# Cleanup
clean:
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.test.yml down -v --remove-orphans

# Kubernetes
k8s-deploy:
	bash k8s/deploy.sh

k8s-delete:
	kubectl delete namespace nexushub
