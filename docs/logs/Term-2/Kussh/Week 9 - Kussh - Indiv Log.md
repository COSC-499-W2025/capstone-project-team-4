# Week 9 (March 1 - March 8) Individual Log 

## Overview
### Week 9
* Added authenticated profile endpoints:
* * GET /api/user-profiles/me to retrieve the current user’s profile.
* * PUT /api/user-profiles/me to create or update the current user’s profile.
* Implemented upsert logic in the user profile service so profile updates automatically create a profile if one does not already exist.
* Built a ProfileDialog component that allows users to edit personal details such as name, location, contact information, and portfolio links.
* Integrated the dialog with the Account page, enabling users to open the profile editor through the Edit Profile button.
* Added a frontend API wrapper (userProfileApi) for interacting with the new /me endpoints.
* Implemented automated frontend and backend tests for the profile editing functionality.

<img width="1086" height="634" alt="Screenshot 2026-03-08 at 8 33 06 PM" src="https://github.com/user-attachments/assets/54d4a61c-24ca-417f-9670-2a9e10d00ab7" />

## PR links
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/245

## Connection to previous weeks 
As planned, started to work on frontend implementation to meet requirements for milestone 3. Also started brainstorming ideas for other features like project thumbnail and project specific analysis as planned but was not able to finish them by this week's deadline. 

## Testing/Debugging tasks
- Tested authenticated profile endpoints using a test database and dependency overrides.
- - Verify GET /api/user-profiles/me returns 404 when a profile does not exist.
- - Verify PUT /api/user-profiles/me creates a new profile for the authenticated user.
- - Verify GET /api/user-profiles/me returns the created profile.
- - Verify PUT /api/user-profiles/me updates an existing profile.
- - Verify profile endpoints require authentication.
<img width="1086" height="266" alt="Screenshot 2026-03-08 at 8 06 13 PM" src="https://github.com/user-attachments/assets/77165346-ce7e-4be9-935d-91bc5a7014fb" />

- Frontend Component Tests (Vitest + React Testing Library)
- - Tested the ProfileDialog component behavior.
- - Verify dialog loads and populates form fields using getMyProfile.
- - Verify empty profile state when no profile exists.
- - Verify profile data is submitted using upsertMyProfile.
- - Verify dialog closes after successful save.
<img width="748" height="389" alt="Screenshot 2026-03-08 at 7 48 50 PM" src="https://github.com/user-attachments/assets/3972a6d7-8553-4cc1-a20a-c1998fde7817" />

- Manual UI Testing
- - Logged in user can access the Account page.
- - Clicking Edit Profile opens the profile dialog.
- - Profile fields can be edited and saved.
- - Saved data persists and reloads correctly from the API.

## Review/Collboration Tasks 
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/244
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/247

## Plans/Goals for Next Week
* Impement project specific analysis frontend.
* Brainstorm ideas and mock up design for web portfolio generation. 
