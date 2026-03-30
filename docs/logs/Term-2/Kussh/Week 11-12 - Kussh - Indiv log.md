# Week 11-12 (March 15 - March 29) Individual Log 

## Overview
- Implemented on-demand chronological skill timeline generation triggered from the portfolio UI
- Removed timeline computation from upload flow to significantly improve upload performance
- Introduced backend endpoint to rebuild skill occurrences only when requested
- Integrated ZIP metadata timestamps as a fallback date source for non-git projects
- Enabled more accurate skill timelines using:
- - Git commit history (if available)
- - ZIP entry timestamps
- - File metadata timestamps
- - Upload date as final fallback

## Backend Changes
- Added rebuild_skill_occurrences_for_project for deferred timeline computation
- Updated _save_skill_occurrences to support multiple date sources (including ZIP metadata)
- Implemented get_zip_entry_dates to extract timestamps from uploaded ZIP files
- Improved date resolution logic to prioritize:
- - Git commit date
- - ZIP metadata date
- - File metadata
- - Upload timestamp
- - Added detailed logging for debugging timeline generation and matching behavior

## Frontend Changes
- Added "View Chronological Timeline" trigger in portfolio UI
- Separated:
- - Skill Snapshot (lightweight, default view)
- - Chronological Timeline (on-demand, computed)
- Fixed project ID mismatches affecting timeline requests
- Improved error handling and loading states for timeline view

## Bug Fixes
- Fixed timeline showing upload date for all skills
- Resolved project ID mismatches between frontend and backend
- Fixed UnboundLocalError and indentation issues in analysis service
- Fixed empty skill occurrence generation due to matching/logging issues

<img width="1076" height="636" alt="Screenshot 2026-03-29 at 10 41 15 PM" src="https://github.com/user-attachments/assets/8c8ec851-8612-42e9-9cff-e69ecc315974" />

## PR links
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/285
- - This PR is larger than usual because it implements a single cohesive feature—accurate skill timelines based on file-level evidence—which required coordinated changes across metadata extraction, ZIP processing, backend services, and timeline generation. The updates are tightly coupled and necessary to ensure correctness (e.g., path normalization and date-source accuracy), and also include end-to-end tests for reliability, making it difficult to split into smaller, independent PRs without breaking functionality.

## Connection to previous weeks 
Finsihed with frontend implementation and wrapped up fixes and bugs for milestone #3 submission. 

## Testing/Debugging tasks

- Backend Test (test_skill_timeline_build.py)
- - Validates rebuilding of skill occurrences from ZIP metadata
- - Uses in-memory SQLite database for isolation
- - Mocks analysis and project repositories to control inputs
- - Creates synthetic ZIP with known file structure and timestamps
- - Ensures skill occurrences are created in DB
- - Verifies date_source is correctly set to "zip_metadata"
- - Confirms timeline response is generated and non-empty
<img width="984" height="232" alt="Screenshot 2026-03-29 at 10 55 56 PM" src="https://github.com/user-attachments/assets/e270aabb-28da-4c7a-a2a5-567b96fa9301" />

- Frontend Test (SkillTimeline.test.jsx)
- - Renders SkillTimeline component with mocked data
- - Simulates user clicking “View Chronological Timeline”
- - Verifies modal opens with correct title
- - Confirms timeline entries are displayed
- - Handles duplicate timestamps using findAllByText
- - Asserts presence of skill counts and chronological data
- - Ensures UI reflects backend-driven timeline correctly
<img width="984" height="232" alt="Screenshot 2026-03-29 at 11 00 47 PM" src="https://github.com/user-attachments/assets/78b403e7-030e-4be5-8478-b3426b925af5" />

- Manual UI Testing
- - End-to-end pipeline testing for resume building, project analysis, skill exctraction, and web portfolio generation. 

## Review/Collboration Tasks 
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/284
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/282
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/281

## Plans/Goals for Next Week
* Project voting
