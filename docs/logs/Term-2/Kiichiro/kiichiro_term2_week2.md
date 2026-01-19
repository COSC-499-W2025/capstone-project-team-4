## Week 2 - January 13-19, 2026

### Overview

This week, I focused on improving the API's timestamp handling by implementing four distinct timestamp fields to accurately track project lifecycle events, from upload to actual project inception.

### Coding Tasks

#### Multi-Timestamp Implementation for Analysis Results

**Branch:** `fix/timestamp-date-created`  
**Repository:** [COSC-499-W2025/cosc-499-w2025-capstone-project-project-starter](https://github.com/COSC-499-W2025/cosc-499-w2025-capstone-project-project-starter)  
**PR:** https://github.com/COSC-499-W2025/capstone-project-team-4/pull/143

**Problem Identified:**

- The API response's `created_at` field was showing ZIP extraction time instead of the actual project creation date
- Users needed to distinguish between when a ZIP was uploaded vs. when the project actually started

**Solution Implemented:**

- Added four timestamp fields to `AnalysisResult` schema:
  - `zip_uploaded_at`: Timestamp when ZIP file was uploaded to API
  - `first_file_created`: Earliest file date extracted from ZIP metadata
  - `first_commit_date`: First Git commit timestamp (nullable if not a Git repository)
  - `project_started_at`: Minimum of `first_file_created` and `first_commit_date` representing actual project inception

**Files Modified:**

- `backend/src/models/schemas/analysis.py`
  - Updated `AnalysisResult` schema with four new timestamp fields
  - Added `json_schema_extra` with explicit example showing distinct timestamps
- `backend/src/services/analysis_service.py`
  - Implemented `get_earliest_file_date_from_zip()` helper function to extract oldest file date from ZIP metadata
  - Modified `analyze_from_zip()` to capture upload time and earliest file date
  - Updated `_run_analysis_pipeline()` to accept and calculate all four timestamps
  - Modified `get_analysis_result()` with placeholder values for database retrieval
- `backend/src/core/analyzers/contributor.py`
  - Added `get_first_commit_date()` function to retrieve first Git commit timestamp
  - Preserved existing `get_project_creation_date()` for fallback logic

#### Timestamp Verification

- Verified `zip_uploaded_at` correctly captures current time when ZIP is uploaded
- Confirmed `first_file_created` successfully extracts oldest file date from ZIP internal metadata using `zipfile.ZipFile.infolist()`
- Tested `first_commit_date` returns correct Git first commit when repository is present, returns `None` for non-Git projects
- Validated `project_started_at` correctly selects minimum between file creation and first commit dates

#### Swagger Documentation Issue Resolution

**Issue:** Swagger UI was showing duplicate 201 responses with identical placeholder timestamps, causing confusion
**Root Cause:** FastAPI auto-generates two 201 entries (one from `status_code=201`, one from `response_model`), and auto-generated examples used same timestamp for all fields
**Solution:** Added explicit `json_schema_extra` example to schema showing four distinct, meaningful timestamps

### Review & Collaboration Tasks

- [PR #138](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/138) - Frontend: Home page implementation and testing infrastructure

#### Team Meeting

- Discussed weekly log structure improvements based on TA feedback
- Aligned on new `Term-2` folder organization for individual logs

### Connection to Previous Work

Building on Week 1's focus on API layer development, this week addressed a critical data accuracy issue where timestamps were misleading users about project age and history.

### Plan for Next Week

- [x] Create and submit PR for timestamp implementation
- [ ] Address code review feedback regarding commit functionality issues
- [ ] Continue working on evaluation criteria updates related to commit analysis
- [ ] Consider database migration to persist new timestamp fields
- [ ] Update API documentation with timestamp field descriptions

### Blockers & Questions

- **Commit functionality issue**: PR review identified issues with commit-related features. This is related to ongoing evaluation criteria updates and will be addressed in continued development
- Database schema update needed to persist all four timestamps (currently only returned in API response)
- Need to verify `file_repo.get_earliest_file_date()` method exists before `get_analysis_result()` can work properly

---

**Hours Worked:** ~8 hours
