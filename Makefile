.PHONY: up up-build down down-v logs ps test test-backend test-backend-cov test-frontend test-frontend-cov test-all shell-backend shell-frontend health lint-backend lint-frontend lint typecheck-backend

# Allow shorthand: make test path/to/test
ifneq (,$(filter test,$(MAKECMDGOALS)))
TEST_GOAL := $(filter-out test,$(MAKECMDGOALS))
TEST_PATH := $(subst \,/,$(TEST_GOAL))
IS_FRONTEND := $(filter frontend/%,$(TEST_PATH))
BACKEND_TEST_PATH := $(patsubst backend/%,%,$(TEST_PATH))
FRONTEND_TEST_PATH := $(patsubst frontend/%,%,$(TEST_PATH))
.PHONY: $(TEST_GOAL)
$(TEST_GOAL):
	@:
endif

# Allow shorthand: make lint path/to/file
ifneq (,$(filter lint,$(MAKECMDGOALS)))
LINT_GOAL := $(filter-out lint,$(MAKECMDGOALS))
LINT_PATH := $(subst \,/,$(LINT_GOAL))
IS_FRONTEND_LINT := $(filter frontend/%,$(LINT_PATH))
BACKEND_LINT_PATH := $(patsubst backend/%,%,$(LINT_PATH))
FRONTEND_LINT_PATH := $(patsubst frontend/%,%,$(LINT_PATH))
.PHONY: $(LINT_GOAL)
$(LINT_GOAL):
	@:
endif

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

# Run backend tests with coverage report
test-backend-cov:
	docker compose exec -T backend pytest tests --cov=src --cov-report=term-missing --cov-report=html -v


# Run frontend tests
test-frontend:
	docker compose exec -T frontend npm run test:run

# Run frontend tests with coverage report
test-frontend-cov:
	docker compose exec -T frontend npm run test:coverage

# Lint backend code
lint-backend:
	docker compose exec -T backend ruff check src tests

# Lint specific path, or lint all if no args
# make lint                        → lint both backend and frontend
# make lint backend/src/api/main.py → ruff check on that file
# make lint frontend/src/          → npm run lint on frontend
lint:
ifeq ($(strip $(LINT_GOAL)),)
	docker compose exec -T backend ruff check src tests
	docker compose exec -T frontend npm run lint
else ifneq ($(strip $(IS_FRONTEND_LINT)),)
	docker compose exec -T frontend npm run lint -- $(FRONTEND_LINT_PATH)
else
	docker compose exec -T backend ruff check $(BACKEND_LINT_PATH)
endif

# Lint frontend code
lint-frontend:
	docker compose exec -T frontend npm run lint

# Run backend type checks
typecheck-backend:
	docker compose exec -T backend mypy src


# Run all tests, or a specific backend test when given a path
test:
ifeq ($(strip $(TEST_GOAL)),)
	docker compose exec -T backend pytest tests -v
	docker compose exec -T frontend npm run test:run
else ifneq ($(strip $(IS_FRONTEND)),)
	docker compose exec -T frontend npm run test:run -- $(FRONTEND_TEST_PATH)
else
	docker compose exec -T backend pytest $(BACKEND_TEST_PATH) -v
endif

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
	@echo "Frontend:" && curl -sf http://localhost:5173 -o /dev/null && echo "OK" || echo "Not ready"
