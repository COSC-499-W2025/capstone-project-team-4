# Week 10 (Mar 8th - Mar 15th) Individual Log

## Overview
This week I focused on implementing the Portfolio page frontend skeleton and fixing two backend bugs. The Portfolio page establishes the full component structure including TopProjects, SkillTimeline, ActivityHeatmap, PrivateModeEditor, and PublicModeView as placeholder components ready for future implementation. 
The backend fixes addressed duplicate `files_analyzed` counts on re-upload and projects being stored with a `NULL` `user_id`.

## Coding Tasks
(image is glitched so I can't upload it) 
- [x] Assigning people to tasks
- [x] Coding
- [x] Reviewing teammate's code
- [x] Testing for your code
- [x] Testing teammate's code
- [x] Team meetings

## PR Links
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/260
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/265

## Connections to Previous Weeks
This week builds on the backend analysis pipeline work from previous milestones. The Portfolio page connects to the existing `POST /api/portfolio/generate` endpoint developed in earlier weeks. The `user_id` bug fix ensures projects are correctly associated with the authenticated user, which is a prerequisite for the portfolio to display the right data.

## Testing/Debugging Tasks
- Added `Portfolio.test.jsx` with 7 tests covering loading state, title/summary render, stat card labels, API error handling, default private mode, and public/private toggle
- Added `TopProjects.test.jsx` with 8 tests covering section heading, empty state, top 3 sorting, rank badges, language tags, resume highlights, custom name override, and live demo link
- All 15 tests passing locally with Vitest
- Debugged duplicate `files_analyzed` bug — root cause was both `incremental_base` and `cached_project` clone paths running back-to-back on re-upload
- Debugged `NULL` `user_id` bug — root cause was `user_id` being passed into `analyze_from_zip` but not forwarded to `_run_analysis_pipeline`

## Review/Collaboration Tasks
- Responded to PR review feedback resolving lint errors across Portfolio skeleton components and `useFileUpload.js`
- Reviewed PR #252, #254

## Plans/Goals for Next Week
- Continue Milestone #3 frontend work
- Improve upon changes from Peer Evaluation 
