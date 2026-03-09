# Week 9 (Mar 1st - Mar 8th) Individual Log

## Overview
This week I focused on implementing the Manage Data Settings feature for the Account page. This included building a privacy settings modal that allows users to view and update their data collection and AI generation preferences, which are was properly sent to the backend. I also implemented consent flow logic so that users who opt out of data collection are re-prompted 
with the data privacy consent modal on their next upload. Additionally, I reviewed a teammate's PR to maintain code quality.

## Coding Tasks
<img width="858" height="516" alt="image" src="https://github.com/user-attachments/assets/e5eba05e-052e-4f39-9a63-d0f1dd07898b" />

## PR Links
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/247

## Connections to Previous Weeks
This week builds on previous weeks as we start to implement frontend to our endpoints we have developed from the previous milestones, The Manage Data modal connects the frotnend privacy toggles to the existing backend endpoint `/api/privacy-settings/{user_id}`. 
The consent reset logic ties into the `useFileUpload` hook's existing `consentGiven` local storage state to ensure the upload flow and privacy settings remain.

## Testing/Debugging Tasks
* Added 2 tests to `useFileUpload.test.js` covering `handleConsentAccept` - verifies backend privacy call on consent and that upload proceeds if the call fails
* Added `Account.test.jsx` with 6 tests covering the Manage Data modal - toggle behaviour, localStorage reset on opt-out, and error handling
* All 8 tests passing locally with Vitest

## Review/Collaboration Tasks
* Reviewed PR #242
 
## Plans/Goals for Next Week
* Continue Milestone #3 frontend work
* Begin implementing the Resume page (`/resume`) 
