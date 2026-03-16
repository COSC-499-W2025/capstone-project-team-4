# Week 10 (March 8 2026 - March 15 2026)

## Overview

For this week, I was working on adding password changes & an activity heatmap.

## Coding Tasks
<img width="1492" height="734" alt="T2-Week-9-Log" src="https://github.com/user-attachments/assets/f7e3044f-1b6a-4ac4-85c5-70f7c6872a99" />

### Add password changes
[Pull 252](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/252)

- Add a popup that allows users to change their current password
- Also fixed the front end on the user's account page so that it looks a bit nicer!

### Adding the activity heatmap
[Pull 270](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/270)

- Made a per-project heatmap that has coloured squares on the frontend
- Also implemented API endpoints for new snapshot creation.


## Blockers and Solutions

- **Issue**: Main issue was some API endpoints (especially for the heatmap) didn't have an appropriate one for heatmaps specifically.
- **Solution**: Created a new API endpoint for how snapshots are taken.

## Plan for Next Week

- Definitely fix more for the heatmap. Right now, it only seems to get from the top 3 projects and it would be nice to have more flexibility.
- Also, due to the Heatmap's complexity, I need to fix some bugs for sure.
