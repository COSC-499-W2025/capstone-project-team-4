## Week 4+5 – Individual Log (Takumi)

### Overview
Throughout Week 4-5, I implemented snapshot creation and comparison flows, refined snapshot summaries, and stabilized related tests for backend integration.
<img width="1114" height="643" alt="Screenshot 2026-02-08 at 18 05 24" src="https://github.com/user-attachments/assets/43e3091d-b27d-44aa-8b75-71f689f74212" />



### Coding Tasks
- Added snapshot creation endpoint that generates both current and midpoint snapshots in one call.
- Implemented snapshot service logic to resolve commits, build summaries, and persist snapshots.
- Added comparison endpoint to compute deltas between current and midpoint snapshots by project.
- Refined snapshot summary payloads and response schemas.

### Testing and Debugging Tasks
- Wrote and updated unit tests for snapshot service and routes.
- Debugged compare contract changes and aligned tests with API shape.
- Validated snapshot summary fields and deltas.

### Reviewing and Collaboration Tasks
Reviewed PRs related to authentication, contributions, and nested ZIP file analysis.

### Connection to Previous Week
After prioritizing a user friendly UI for the peer review session in week 3, I shifted my focus on backend snapshot creation and comparison so that UI has meaningful evolution data to display without extra manual steps.

### Plan for Next Week
- Start working on the GET /portfolio/{id}, POST /portfolio/generate, and POST /portfolio/{id}/edit.


### Issues / Blockers
- Snapshot comparison contract changed during the sprint, causing temporary mismatches.
- Snapshot creation depends on ZIPs containing `.git` history and can fail otherwise.
- Large/multi-folder ZIPs and snapshot table resets led to inconsistent results.
