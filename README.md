[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20510500&assignment_repo_type=AssignmentRepo)
# Capstone Project Team 4
## 🚀 Quick Start

### Prerequisites
- Python 3.11.0
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
# This command will create HTML report at /htmlcov
pytest --cov=src --cov-report=html


# View coverage report
open htmlcov/index.html

# For windows : start htmlcov/index.html
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
docker compose exec app pytest --cov=src --cov-report=term-missing

# remove container
docker compose down
```

## 📖 Documentation
- [Contributing Guidelines](.github/CONTRIBUTING.md)
- [CLI Documentation](https://github.com/COSC-499-W2025/capstone-project-team-4/blob/docs/update_to_diagram/docs/design/CLI%20Documentation.md)
- [Team Contract](https://github.com/COSC-499-W2025/capstone-project-team-4/blob/docs/update_to_diagram/docs/contract/CapstoneTeamContract.pdf)
- ## Revised Diagram Links
- [Revised DFD Level 1](https://github.com/COSC-499-W2025/capstone-project-team-4/blob/docs/update_to_diagram/docs/design/dfd-level-1-revised.png)
- [Final System Architecture](https://github.com/COSC-499-W2025/capstone-project-team-4/blob/docs/update_to_diagram/docs/design/SystemArchitectureDiagram.png)
- [Analysis Pipeline](https://github.com/COSC-499-W2025/capstone-project-team-4/blob/docs/update_to_diagram/docs/design/Analysis%20Pipeline.png)
- [New WBS Table](https://github.com/COSC-499-W2025/capstone-project-team-4/blob/docs/update_to_diagram/docs/design/WBS.txt)

