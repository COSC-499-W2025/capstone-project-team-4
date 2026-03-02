# Team 4 Term 2 Week 3 Log (Jan 18 - 25) 

## Milestone recapped
This week’s work focused on major backend and frontend improvements to support more robust file handling, data analysis and user experience around project uploads and contributor statistics. We completed multiple merges that advanced core features for database support, ZIP file processing which included nested projects in zips, API correctness around contributor data and frontend UI pages for upload and summary views 

## Plan To-Dos for Next Cycle 
For the next cycle, we will: 
Work on issues in github backlog 
Improve system based on feedback from peer review 
Work on leftover topics from milestone 2 requirements 

## Burnup chart

## Features Planned for this Milestone

Nested Project Analytics: support for projects contained inside multiple layers of ZIPs.


Normalized Contributor Tracking: unique contributor identities aggregated properly.


UI Upload & Summary Pages: frontend pages that connect uploads to backend API endpoints.
Database Migration: replace SQLite with PostgreSQL for better scaling and deployment support.


## Project Board Tasks Associated with those Features
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/135
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/136
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/137
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/138
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/139
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/140
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/143
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/144

## Test Reports
This week’s manual testing focused on:
Verifying nested ZIP analysis via APi calls, with correct project_id assignment
Confirming contributor aggregation fixes by uploading test repos with multiple commit identities and matching with github’s online number
