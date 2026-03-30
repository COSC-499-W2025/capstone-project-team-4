# Week 11 (March 15 2026 - March 22 2026) & Week 12 (March 22 2026 - March 29 2026)

## Overview

For these past 2 weeks, I've been working on creating the activity heatmap for the frontend, fixing the heatmeap with commits instead of snapshots, and
critical bug fixes. Along with the Milestone #3 video demo.

## Coding Tasks
<img width="1198" height="696" alt="Week-12-Individual" src="https://github.com/user-attachments/assets/803706f8-1dca-4e04-a0ff-23575489d24d" />


### Add Activity Heatmap Week 11
[Pull 270](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/270)

- Add first version of the activity heatmap
- This heatmap was based on snapshots instead of actual commits.
- Does not have individual hover states for each square on the grid.

### Modify the Heatmap to take Commits
[Pull 276](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/276)

- Modify the heatmap significantly so that it gets a heatmap for each project's commits rather than the snapshot.
- Also had to modify many frontend components such as adding a disclaimer for the user's email being connected to GitHub, etc.
- Had to refactor many files that were using `style=` instead of regular TailwindCSS.


## Blockers and Solutions

- **Issue**: Main issue was that because I made a new branch off of someone else's for PR 276, it resulted in an extra large PR.
- **Solution**: Thankfully, merging it to `development` worked just fine.

## Plan for Next Week

- Since we're almost done, it's time to just focus on bug fixing rather than adding new features.
