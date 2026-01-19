## Week 2 – Consent Manager Database & CLI Refactor

### Overview
This week, I focused on backend infrastructure work for the Consent Manager feature, including implementing the database layer and refactoring the main application CLI. The goal was to ensure proper routing, maintainability, and alignment with the project’s FastAPI architecture while identifying and addressing missing functionality introduced during the refactor.

### Coding Tasks
[PR #143](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/146)
#### Consent Manager Database Implementation
- Designed and implemented the database schema to support consent tracking, including consent state, timestamps, and user association
- Integrated consent-related models into the existing database initialization workflow
- Ensured the database design supports privacy-first requirements and future extensibility (e.g., consent updates or revocation)

#### `main.py` CLI Refactor
- Rebuilt the `main.py` CLI to follow proper application routing to new filepath.
- Aligned the CLI structure with the rest of the backend architecture

#### Feature Gap Identification
- Identified missing or incomplete features introduced during the CLI refactor
- Documented which consent-related and application-level functionalities need to be reimplemented
- save_files, etc, skill detectors and project summarizers 
- Planned reintroduction of missing logic without compromising the improved structure

### Testing and Debugging Tasks
Consent shows on the fastapi database 

#### Backend Validation
- Verified database initialization occurs correctly on application startup
- Tested CLI execution paths to ensure routes load as expected

### Review / Collaboration Tasks
- Reviewed existing backend patterns to ensure the new CLI structure aligns with team conventions
- Communicated identified missing features to the team to coordinate reimplementation priorities
- Provided clarification on how consent database logic integrates with the application lifecycle

### Plan for Next Week
1. Reimplement missing CLI and backend features identified during the refactor  
2. Implement FastAPI endpoints for managing consent records  
3. Prepare backend interfaces for frontend consent enforcement and upload workflows  
