# Week 11-12 (Mar 15th - Mar 29th) Individual Log

## Overview
This week I focused on Milestone #3 frontend and backend work, delivering three PRs. The main effort was implementing featured project selection on the Portfolio page and allowing users to star projects in Private mode to control what appears in Public view, along with a Choose Projects modal, sort-by-metric buttons, and backend schema updates to support these features. 
I also added a Manage Projects section to the Account page and updated all frontend instances of the old product (Resume Generator) name.

<img width="871" height="510" alt="image" src="https://github.com/user-attachments/assets/cb594c9b-c107-44dc-8313-b3b8d0755aae" />


## PR Links
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/272
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/273
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/275

## Connections to Previous Weeks
This week builds directly on the Portfolio page skeleton and `POST /api/portfolio/generate` endpoint from Week 10. The `is_featured` field and sort metric additions (`file_count`, `contributor_count`, `skill_count`, `total_lines_of_code`) extend the portfolio content JSON established in previous milestones. The Manage Projects feature connects to the existing project delete endpoint and the Account page Manage Data modal from Week 10.

## Testing/Debugging Tasks
- Added 4 new tests to `Account.test.jsx` covering: switching to the Manage Projects view, rendering project names, empty state, and back arrow returning to privacy view
- All tests passing locally with Vitest and through teammate's testing.
- Manually verified starred projects appear correctly in Public mode and that the Choose Projects modal caps selection at 3
- Debugged duplicate project name toggle bug, root cause was `featuredNames` Set using project names instead of IDs; fixed by switching to `featuredIds` using `project.id` 
- Verified Skills stat card now correctly reads from `aggregated_skills` in the portfolio content JSON

## Review/Collaboration Tasks
- Reviewed PR #276 (activity heatmap)
- Reviewed PR #277 (security fix)
- Reviewed PR #278 (custom project name on upload)

## Plans/Goals for Next Week
- Vote on capstone projects
- Wrap up capstone? 
