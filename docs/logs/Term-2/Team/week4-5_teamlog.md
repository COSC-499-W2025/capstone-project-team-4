# Team 4 Term 2 Week 5 
 

## Milestone recapped
These past two weeks have been focused on improving backend performance. The system now supports nested project analysis, allowing multiple projects within a single ZIP file to be added and analyzed independently, and uses project-level caching with file hashing to detect duplicate uploads and reuse prior analysis results. Snapshot creation and comparison features were added to track changes in files and metrics over time, while contributor role identification and ranking logic improved the insight into the contribution impact. We also added authentication logic to support token-based access control within the API. Former tests were reimplemented with proper routing to new file paths along with new testing for new functions added. CLI changes have been implemented using chocolatey and winget in order to load docker and run tests quicker. 

## Plan To-Dos for Next Cycle 
- Add working authentication for each API route
- Update documentation
- Continue finishing the Milestone requirements 

## Burnup chart
<img width="909" height="473" alt="image" src="https://github.com/user-attachments/assets/177b7d73-eeb6-4144-b8c5-09b58fcb9a67" />

## Features Planned for this Milestone
Indicating role of user based on files changed/edited .
Ranking based on data returned from the above function.
Fundamental coding for HTTP based API testing without server running
Nested Project Analysis fixed, allowing for multiple projects to be analyzed at once inside a zip 
Project-level caching and file-level hashing to recognize duplicate project uploads and reuse prior analysis results.
Snapshots creation and comparison: Added two new endpoints for that create both current and midpoint snapshots and compare the current vs midpoint. The comparison returns such as files, lines, and analysis metrics.  
Add authentication by adding token generation and retrieval for each user.

 ## Project Board Tasks Associated with those Features
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/178
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/180
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/185
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/186
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/187
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/189
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/182

These ones not approved and merged yet
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/183
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/184
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/188



## Test Reports
This week we started writing tests again as we neglected to do so. New functions from Week 4 and 5 have pytests associated with each and should provide proper coverage. Each PR should include manual testing instructions and pytest instructions. 
Old tests have been implemented again in a recent PR. 
