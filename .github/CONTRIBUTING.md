# Contributing to Capstone Project Team 4
## 📝 Development Guidelines
This guide will help you get started with contributing to our project.

### Branch Naming
- **Features**: `feature/<descriptive-name>`
- **Bug fixes**: `fix/<issue-description>`
- **Documentation**: `docs/<what-you-are-documenting>`

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description

Examples:
feat: add user authentication
fix: resolve database connection issue
docs: update API documentation
test: add unit tests for validation
```

**Types:**
- `feat` - New features
- `fix` - Bug fixes  
- `docs` - Documentation only
- `test` - Adding/updating tests
- `refactor` - Code restructuring
- `style` - Formatting changes
- `chore` - Maintenance tasks
- `perf` - Performance improvements

### Testing
- Add unit tests for new functionality
- Run tests: `pytest`
- Check coverage: `pytest --cov=src`
- All tests must pass before merging

### Commits & Pull Requests
- Use descriptive commit messages
- Reference issue numbers (e.g., "Fix #123: Add language detection")
- Follow the PR template checklist
- Link related issues in PR description

## 📋 Pre-Commit Checklist

Before submitting a PR, ensure:
- [ ] All tests pass with `pytest`
- [ ] New functionality has tests or plan tests for future
- [ ] Documentation is updated
- [ ] PR template is completed

## 🐛 Reporting Issues

When reporting bugs:
- Use a clear, descriptive title
- Include steps to reproduce
- Provide system information (OS, Python version)
- Include relevant error messages/logs


# 🏃‍♂️ Running the Project 
## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Git
- Docker (optional)

### Setup
1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/capstone-project-team-4.git
   cd capstone-project-team-4
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  
   # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Choose your development method:**
- [Local Development](#local-development) - Direct Python setup
- [Docker Development](#docker-development) - Containerized environment (recommended)

### Local Development
```bash
# Run the main CLI
python -m src.main --help

# Run commands
python -m src.main [OPTIONS] COMMAND [ARGS]...                    

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Docker Development
```bash
# Build and start service
docker compose up --build -d

# Run the main CLI
docker compose exec app python -m src.main --help

# Run commands
docker compose exec app python -m src.main [OPTIONS] COMMAND [ARGS]...  

# Run tests
docker compose exec app pytest

# Run tests with coverage
# This command will create HTML report at /htmlcov
docker compose exec app pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html

# For windows : start htmlcov/index.html

# remove container
docker compose down
```
