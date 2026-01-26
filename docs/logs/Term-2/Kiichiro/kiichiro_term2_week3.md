## Week 3 - January 19-25, 2026


### Summary and Continuity from Previous Week
Building on last week’s work on contribution analysis and metric design, this week focused on resolving discrepancies between GitHub Web UI contribution metrics and locally computed Git statistics. The goal was to ensure that contribution metrics used in later analysis stages are accurate and reproducible without relying on the GitHub API.


### Coding Tasks
- Implemented a Git-based method to reproduce GitHub-aligned Lines added / Lines deleted metrics locally.
- Standardized contribution metric calculation by disabling rename detection to match GitHub’s counting logic:
```git log --no-merges --no-renames --numstat```
- Merged standardized logic into the project via PR #162:
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/162

### Testing and Debugging Tasks
- Investigated large discrepancies between GitHub Web UI metrics and git log --numstat output.
- Verified that discrepancies persisted even when:Restricting analysis to the same branch and time window, Excluding merge commits, Using a non-shallow clone
- Identified the root cause as different handling of file renames and directory moves: GitHub treats renames/moves as delete + add, Default Git detects renames and reports many structural changes as 0/0
- Validated the solution by reproducing GitHub’s weekly contribution statistics exactly at the local level.

### Review and Collaboration Tasks
- Documented findings and shared reproducible CLI commands with the team.
- Discussed implications of rename handling and metric interpretation with team members.
- Merged PR #162 to ensure consistent contribution metrics across the project.
- Approved https://github.com/COSC-499-W2025/capstone-project-team-4/pull/166
- Reviewed https://github.com/COSC-499-W2025/capstone-project-team-4/pull/165

### Plan for Next Week
- Explore alternative contribution metrics that better reflect meaningful development effort.

Hours Worked: ~12 hours
