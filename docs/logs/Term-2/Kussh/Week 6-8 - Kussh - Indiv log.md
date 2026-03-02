# Week 6-8 (Feb 9 - March 1) Individual Log 

## Overview
### Week 6
* new ProjectThumbnail ORM model (1:1 with Project),
* schema updates to expose thumbnail metadata (has_thumbnail, thumbnail_updated_at, thumbnail_endpoint),
* new PUT /api/projects/{project_id}/thumbnail endpoint with validation and upsert logic.
* The endpoint allows image types (PNG/JPEG/WEBP), a 5MB size limit, generates a SHA256 etag, and ensures only one thumbnail exists per project (replace-on-upload behavior).

### Week 7 (Reading Break)
* Incorporated feedback from Aliff on Project Thumbnail PR
* * Implement GET /api/projects/{project_id}/thumbnail
  * Returns stored thumbnail image bytes,
  * sets correct Content-Type header,
  * returns ETag header (SHA256 hash),
  * supports conditional requests using If-None-Match,
  * returns 304 Not Modified when ETag matches
  * returns 404 if thumbnail does not exist

* * Implement DELETE /api/projects/{project_id}/thumbnail
  * removes thumbnail record from database
  * returns 204 No Content on success
  * returns 404 if thumbnail does not exist

* * Add automated tests covering:
  * GET success case
  * GET 404 when missing
  * GET 304 behavior with matching ETag
  * DELETE success
  * DELETE 404 when missing

### Week 8
* Introduced a new Textual Project Showcase API endpoint to meet milestone 2 requirement. 
* * Endpoint: GET /projects/{project_id}/textual-project-showcase
  * returns a lightweight, portfolio-ready view of analyzed project data using the newly introduced TextualProjectShowcaseResponse schema.
  * Added TextualProjectShowcaseResponse schema in analysis.py
  * Implemented ProjectService.get_textual_project_showcase()
  * Added new route in projects.py
  * Ensure consistent ProjectNotFoundError handling
  * FIX: missing field mapping in get_project() that previously caused empty lists
  * FIX: Added safe serialization logic to prevent ORM objects from causing 500 errors

## Coding Tasks
<img width="1082" height="637" alt="Screenshot 2026-03-01 at 7 35 51 PM" src="https://github.com/user-attachments/assets/7a46551f-9c77-435b-9b7a-e0f388d12fb8" />

## PR links
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/229
- - **Oversized PR Explanation:** Oversized PR Explanation: This PR shows 921 insertions because, at the time it was created, the thumbnail feature branch had not yet been merged into development, and this branch already contained those thumbnail commits in its history. Although the thumbnail implementation (approximately 680 lines) has since been merged separately, GitHub continues to count those changes in this PR due to branch ancestry and comparison timing, not because they are newly introduced here. The actual new insertions specific to this PR are approximately 241 lines. Tested and verified that development branch and both features works fine.
   
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/211
- - **Oversized PR Explanation:** This PR exceeds 500 lines due to the interconnected nature of the thumbnail feature.
  - Implementing this functionality required changes across multiple layers of the system, including:
  - New ORM model and schema definitions, Database relationship updates, Service-layer logic, API route implementations (PUT, GET with ETag support, DELETE), Associated tests and validations
  - Originally, these components were developed across multiple smaller branches. However, due to dependency overlap between the model, service, and route layers, the changes had to be consolidated into a single branch to ensure consistency and avoid integration conflicts.
  - Although the PR is larger than usual, all changes are directly related to the thumbnail feature.

## Connection to previous weeks 
Week 5 we decided to change focus from frontend development to backend to ensure meeting requirements for milestone 2. The shift in focus allows us to better meet these requirements and ensure a proper submission. 

## Testing/Debugging tasks
- - Implemented pytest:
  - tests/test_textual_project_showcase.py
  - tests/test_project_thumbnail_get.py
  - tests/test_project_thumbnail_delete.py
  - tests/test_project_thumbnail_put.py
  - tests/test_project_thumbnails_schema.py
 
- - Manual Testing:
  - Thumbnail PUT endpoint
 <img width="732" height="797" alt="552488918-2eac4193-ef36-4ca0-9238-bbdc6a34f229" src="https://github.com/user-attachments/assets/bd8d32d2-dac2-478e-88c4-fe1264ec7948" />

  - Thumbnail GET endpoint
 <img width="718" height="830" alt="553139219-f4556397-d595-4f3e-ae6e-9a6a24e2be5f" src="https://github.com/user-attachments/assets/cbdab658-6f92-4bb4-b155-3cd8e36397d3" />

  - Thumbnail DELETE endpoint
 <img width="718" height="587" alt="553139345-4162e18d-a8d9-42cf-b296-b30e64612a39" src="https://github.com/user-attachments/assets/0034dc20-b899-49c2-9332-7b227f36178c" />

  - Textual Project Showcase - GET endpoint
<img width="719" height="695" alt="Screenshot 2026-03-01 at 9 06 47 PM" src="https://github.com/user-attachments/assets/5337dee0-7270-4937-a719-9e6833311402" />

## Review/Collboration Tasks 
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/201
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/204
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/217
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/221
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/223
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/226 


## Plans/Goals for Next Week
* Study for Quiz 3 (Monday to Wednesday)
* Plan and start frontend implementation for project thumbnail and textual-project-showcase (Wednesday to Sunday)
* Set up manual short_description UI for users to customize and save descriptions per project individually.
* Look into human-in-the-loop feature implementation

