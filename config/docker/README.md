# Docker Configuration

This directory contains Docker configuration files for the project.

## Files
- `Dockerfile` - Docker image definition
- `docker-compose.yml` - Multi-container Docker application definition

## Quick Commands

From the **project root** directory:

### Development
```bash
# Build and start containers
docker compose -f config/docker/docker-compose.yml up --build -d

# View logs
docker compose -f config/docker/docker-compose.yml logs -f

# Stop containers
docker compose -f config/docker/docker-compose.yml down
```

### Running Commands
```bash
# Get shell access
docker compose -f config/docker/docker-compose.yml exec app bash

# Run the main CLI
docker compose -f config/docker/docker-compose.yml exec app python -m src.main --help

# Run tests
docker compose -f config/docker/docker-compose.yml exec app pytest

# Run tests with coverage
docker compose -f config/docker/docker-compose.yml exec app pytest --cov=src --cov-report=term-missing
```

## Alternative: Create Docker Aliases

You can create aliases in your shell profile to simplify commands:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias dcp='docker compose -f config/docker/docker-compose.yml'

# Then use:
dcp up --build -d
dcp exec app python -m src.main --help  
dcp down
```