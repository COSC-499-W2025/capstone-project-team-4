## Week 9 – Individual Log (Takumi)

<img width="1072" height="610" alt="Screenshot 2026-03-08 at 18 46 32" src="https://github.com/user-attachments/assets/dfb6e83c-300b-4353-b6d7-32d345dbb6b4" />


### Overview  

During Week 9, I focused on improving the stability of the system and making the frontend more reliable. I reverted some unstable backend changes from the previous sprint, fixed several frontend crashes, added more tests for components that display analysis results, and investigated a data issue that happened when the PostgreSQL database ran out of disk space in the previous week.

### Testing and Debugging Tasks  
- Reverted the file upload logic to read the whole file at once, since the streaming method added in the previous sprint caused instability.
- Removed the custom proxy timeout settings that were added earlier, as they were unnecessary and could hide real timeout problems.
- Added error handling when reading data from localStorage so the app does not crash if the saved data is corrupted.
- Fixed a crash in the contributor progress bar when the contributor data had a value of zero.
- Cleaned up the dropzone component by removing leftover debug logs and an unused import.

### Reviewing and Collaboration Tasks  
Reviewed [PR#239](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/239) and [PR#240](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/240)

### Connection to Previous Week  
Last week, I completed the portfolio endpoint and our team finished Milestone 2. This week, I started focusing more on the frontend part of the project.

### Plan for Next Week  
Integrate the endpoints we built in Milestone 2 into the frontend.

### Issues / Blockers  
-Incorrect analysis results were returned for some previously uploaded ZIP files because old cached data in the database became corrupted when the disk was full last sprint. Resetting the database in the development environment will fix this issue.
