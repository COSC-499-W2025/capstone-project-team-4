## Week 12 – Individual Log (Takumi)

<img width="1126" height="611" alt="Screenshot 2026-03-29 at 20 32 36" src="https://github.com/user-attachments/assets/7b586cb7-c716-4786-9a0a-37b75bb9239c" />

### Overview

This week I worked on improving the project history page by adding project deletion, a Delete All option, and a search bar. I also wrote tests to make sure these features work correctly.

### Testing and Debugging Tasks

Wrote and updated tests across History.test.jsx and useFileUpload.test.js to cover search filtering, the no-results empty state, Delete All confirm/cancel flow, parallel API calls on bulk delete, and individual deletion behaviour. Also fixed a race condition in an existing test where the loadPreviousProjects mount effect was consuming a mocked API response intended for a later call inside handleConsentAccept, causing it to call PUT /api/privacy-settings/undefined. The fix involved draining async mount effects before setting up subsequent mocks.

### Reviewing and Collaboration Tasks
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/278
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/279

### Connection to Previous Week
Last week, we received a lot of feedback from the peer testing session, so this week we focused on implementing and updating our system based on those comments.

### Plan for Next Week  
Voting

### Issues / Blockers
- The number of projects shown on the Generator page changed a few times (5 → 6 → 4), and the delete button was added, removed, and added again, so we had to update the code and tests each time.
- The navigation bar overflowed because the label "Coding Project Analyzer" was too long and repeated the brand name, so we adjusted the layout and moved account controls to the right.
