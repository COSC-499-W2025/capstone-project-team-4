# Backend Tests

This directory contains automated tests for the backend API, specifically for the snapshot creation and comparison features.

## Test Files

### `conftest.py`
Contains pytest fixtures used across all test files:
- `test_db`: In-memory SQLite database for isolated testing
- `client`: FastAPI TestClient with dependency injection
- `temp_dir`: Temporary directory for test files
- `sample_project`: Pre-created sample project in the test database
- `git_repo_zip`: Sample ZIP file with a git repository (15 commits)

### `test_snapshot_creation.py`
Tests for the snapshot creation feature in `/api/projects/analyze/upload`:

**Tests:**
- ✅ Snapshot creation with valid git repository
- ✅ Failure without git history (.git directory)
- ✅ Failure with insufficient commits (< 10)
- ✅ Snapshots not created when flag is disabled
- ✅ Correct naming convention (project-Mid, project-Late)
- ✅ Snapshots created at correct commit points (60%, 85%)
- ✅ Custom project name handling

**Coverage:**
- Valid snapshot creation flow
- Error handling (missing .git, too few commits)
- Snapshot naming and suffixes
- Database persistence verification

### `test_snapshot_comparison.py`
Tests for the snapshot comparison feature in `/api/test-data/snapshots/compare`:

**Tests:**
- ✅ Compare snapshots by project ID
- ✅ Compare snapshots by project name
- ✅ Missing parameter validation
- ✅ Non-existent project error handling
- ✅ Metric comparison structure verification
- ✅ Snapshot metrics structure verification
- ✅ Comparison summary generation
- ✅ Percent change calculation
- ✅ No changes scenario (identical projects)

**Coverage:**
- Query by ID vs name
- Response schema validation
- Metric calculations (change, percent_change)
- New items detection (languages, frameworks, libraries)
- Error cases (404, 400)

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run specific test file
```bash
pytest tests/test_snapshot_creation.py
pytest tests/test_snapshot_comparison.py
```

### Run specific test
```bash
pytest tests/test_snapshot_creation.py::test_snapshot_creation_with_valid_git_repo
pytest tests/test_snapshot_comparison.py::test_compare_snapshots_by_id
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

## Test Structure

```
backend/
├── pytest.ini                    # Pytest configuration
├── tests/
│   ├── __init__.py
│   ├── README.md                 # This file
│   ├── conftest.py              # Shared fixtures
│   ├── test_snapshot_creation.py     # Snapshot creation tests
│   └── test_snapshot_comparison.py   # Snapshot comparison tests
└── src/                         # Source code being tested
```

## Key Features Tested

### Snapshot Creation
1. **Git History Validation**: Ensures .git directory exists and has at least 10 commits
2. **Snapshot Points**: Creates 2 snapshots at 60% (Mid) and 85% (Late) of commit history
3. **Naming Convention**: Follows pattern `{project_name}-{Mid|Late}`
4. **Database Persistence**: Verifies all 3 projects (main + 2 snapshots) are saved

### Snapshot Comparison
1. **Flexible Querying**: Supports both ID and name-based lookups
2. **Metric Calculations**: Computes absolute and percentage changes
3. **Progression Detection**: Identifies new languages, frameworks, and libraries
4. **Summary Generation**: Creates human-readable comparison summaries

## Dependencies

Tests use:
- `pytest`: Test framework
- `fastapi.testclient`: API testing
- `sqlalchemy`: Database testing with in-memory SQLite
- Standard library: `tempfile`, `zipfile`, `subprocess` for fixtures

## Notes

- Tests use in-memory SQLite database (not PostgreSQL) for speed and isolation
- Each test has its own database session that's cleaned up after
- Git repositories are created programmatically in temp directories
- All tests are independent and can run in any order
