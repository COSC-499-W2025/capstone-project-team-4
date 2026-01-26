# Week 3 - January 19-15 2026

## Overview
This week, I focused on implementing frontend for the User Profiles Page. Additionally, I also configured a centralized Axios API client with base URL, defaults, and response error logging.

## Coding Tasks

- Implemented frontend for User Profiles page
- Refactored layout into reusable components (e.g., ProfileCard.jsx, ProfilesGrid.jsx) and aligned imports with the @/components/... alias pattern.
- Added API helper to fetch paginated user profiles from /api/user-profiles.

## Testing and Debugging Tasks

- Added Vitest test suites for Login and Signup pages and accessibility checks.
- Debugged test failures by fixing heading semantics, label collisions, and stabilizing the test environment (cleanup hooks, Radix/ResizeObserver support).
- Achieved successful runs on all tests. 

## Review/Collaboration Tasks
- Reviewed:
  - https://github.com/COSC-499-W2025/capstone-project-team-4/pull/147#pullrequestreview-3676644113
  - https://github.com/COSC-499-W2025/capstone-project-team-4/pull/167

## My PR: https://github.com/COSC-499-W2025/capstone-project-team-4/pull/168

## Connection to Previous Week
I spend last week creating the frontend for login and signup page. Now having worked on User Profiles, I can start working on account setting page (FRONTEND) and POST method for user profile information (BACKEND). 
  
## Plan for Next Week

- BACKEND - work on POST method to recieve user profile information from user.
- Update UI to be more responsive and follow usabilty principles
- FRONTEND - Implement "Account Settings" page 
