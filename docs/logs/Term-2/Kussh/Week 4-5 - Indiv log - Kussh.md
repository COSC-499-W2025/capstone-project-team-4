# Week 4-5 (Jan 25 - Feb 8) Individual Log 

## Overview
### Week 4
* Added `ProfileDialog.jsx` to support creating and editing user profile information and implemented form fields
* Wired dialog to profile API for create functionality.
* Enabled basic profile creation flow from the UI.
* Added profile card display after successful profile creation in a grid.
* Allowed clicking a profile card to reopen the dialog in edit mode (update not implemented yet).
* Updated `ProfilesPage.jsx` to support the new profile flow.
* Improved layout and responsiveness in:
  * `ProfileCard.jsx`
  * `ProfilesGrid.jsx`
  * `ProfilesHero.jsx`
  * `ProfilesHeader.jsx`
* Updated `user_profile_API` to handle profile-related requests.
* Merged last week’s Profiles page base components into the same PR for a complete, testable UI flow.

### Week 5
* Began work on the milestone requirement to allow users to associate a portfolio image with a project to use as a thumbnail.
* Focused on planning the backend API structure and overall implementation approach.
* Code is partially complete and final implementation and merge are planned for next week.

## Coding Tasks
<img width="1083" height="636" alt="Screenshot 2026-02-08 at 10 13 14 PM" src="https://github.com/user-attachments/assets/772eff56-4e4e-4814-ba03-23b66ad2f70c" />

## PR links
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/175
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/173

## Connection to previous weeks 
week 4’s work builds directly on the Profiles page foundation created in week 3. After setting up the base layout, reusable components, and API client, 
I extended the feature by adding the ProfileDialog and completing the basic profile creation flow. This allowed the Profiles page to move from a static UI to a functional, 
testable interface. The following week 5’s work then shifted focus from frontend to backend to be able to meet milestone 2 requirements, and started working on requirement
which involves adding portfolio image thumbnails to projects.

## Testing/Debugging tasks
- Implemented vitest for edit profile dialogue box
<img width="1470" height="956" alt="543512259-2e4bb9a7-188a-4c46-9862-a01991626a66" src="https://github.com/user-attachments/assets/232408d2-c101-4c10-9d3f-1af8a26b58ef" />

## Review/Collboration Tasks 
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/189
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/188
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/185
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/176

## Plans/Goals for Next Week
* Complete the backend implementation for project thumbnail uploads.
* Add endpoints to upload, fetch, and delete a project’s portfolio image.
* Implement database changes to store thumbnail references.
* Integrate thumbnail support into the existing project API responses.
* Write tests for the new thumbnail functionality.
* Perform manual testing of the full upload → fetch → delete flow.
* Plan for implementing textual information about project as showcase and resume item (mileston requirement: 9 & 10)
