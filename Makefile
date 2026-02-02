.PHONY: up down logs ps test test-backend test-frontend test-all shell-backend shell-frontend

# Start all services
up:
	docker compose up -d

# Start with build
up-build:
	docker compose up -d --build

# Stop all services
down:
	docker compose down

# Stop and remove volumes
down-v:
	docker compose down -v

# View logs
logs:
	docker compose logs -f

# Show container status
ps:
	docker compose ps

# Run backend tests
test-backend:
	docker compose exec -T backend pytest tests -v

# Run backend tests with coverage
test-backend-cov:
	docker compose exec -T backend pytest tests --cov=src --cov-report=term-missing -v

# Run frontend tests
test-frontend:
	docker compose exec -T frontend npm run test:run

# Run frontend tests with coverage
test-frontend-cov:
	docker compose exec -T frontend npm run test:coverage

# Run all tests
test-all: test-backend test-frontend

# Alias for test-all
test: test-all

# Run backend tests with coverage report
test-report:
	docker compose exec -T backend pytest tests --cov=src --cov-report=term-missing --cov-report=html -v

# Open shell in backend container
shell-backend:
	docker compose exec backend bash

# Open shell in frontend container
shell-frontend:
	docker compose exec frontend sh

# Check service health
health:
	@echo "Database:" && docker compose exec -T db pg_isready -U workmine -d workmine || echo "Not ready"
	@echo "Backend:" && curl -sf http://localhost:8000/health && echo " OK" || echo "Not ready"
	@echo "Frontend:" && curl -sf http://localhost:5173 > /dev/null && echo "OK" || echo "Not ready"
