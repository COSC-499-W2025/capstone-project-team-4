# Team 4 Term 2 Week 6-8 

## Milestone recapped
In the past two weeks, the team focused on implementing several key features and improvements to enhance the project and backend performance.  We introduced Image thumbnails associated with projects, Changes to contributor analysis, implemented features that tracks file paths associated with specific contributors, which allows us to generate more accurate contributor rankings based on their code contributions. Additionally, we added new endpoints for the portfolio with edit and get endpoints now available, along with resume generation with different filetype exportations (markdown, html, pdf) with project information all put on there. We also added incremental addition to projects to ensure better performance so as to not have to reanalyze an entire project again. These enhancements were accomplished through testing manually and by units and were to test new features to ensure their reliability and functionality. We now transition to Milestone #3 where we will work on our frontend implementation. 

Completed all milestone #2 major tasks

### API endpoints 
* Portfolio APIs were built out so users can generate, view, and edit portfolios, including support for customizing how projects appear.
* Resume APIs were added for a “full resume” workflow, including generation and export, backed by clearer schemas/templates.
* Project media/display APIs were expanded with:
* Project thumbnail endpoints (upload/set, fetch, delete) plus metadata + caching considerations.
* A textual project showcase endpoint designed to return “portfolio-ready” project details.
* Analysis/contributor-related endpoints were improved, including integrated/individual analysis flow and contribution ranking.
* Snapshot endpoints were implemented/extended to support creating snapshots, comparing snapshots, and deleting snapshots.
* Portfolio endpoints were implemented to allow users to generate, update, and publicly share a complete portfolio built from their analyzed project data.
### Major fixes & improvements
* Reliability fixes like correcting contributor analysis file paths, reducing errors caused by incorrect filesystem references.
* Cleanup/refactoring such as removing duplicated API logic, making the backend easier to maintain.
* Strong emphasis on quality and stability:
* More automated tests for core workflows (resume export, portfolio customization, analysis endpoints, thumbnails).
* Improved CI and automation (lint/type checks, PR automation, API/contract testing), making merges safer and regressions less likely.
* Better developer/setup experience via Docker/Linux compatibility fixes and convenience tooling (e.g., Makefile).

## Plan To-Dos for Next Cycle 
Plan and allocate work for Milestone #3
Fix bugs from merging in development branch 

## Burnup chart
<img width="918" height="466" alt="image" src="https://github.com/user-attachments/assets/05a6dac5-4267-4ab9-8925-eb6630232d3c" />

We have a lot of old issues we had not closed yet. After proper addressing to verify it had been completed, then we will close. 

## Features Planned for this Milestone
Listed as the endpoints above 

 ## Project Board Tasks Associated with those Features
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/213
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/217
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/218
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/202
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/207
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/223
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/224
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/227
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/229
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/211
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/221
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/216
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/215
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/214
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/207 
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/204 
https://github.com/COSC-499-W2025/capstone-project-team-4/pull/203
 https://github.com/COSC-499-W2025/capstone-project-team-4/pull/199
 https://github.com/COSC-499-W2025/capstone-project-team-4/pull/198
 https://github.com/COSC-499-W2025/capstone-project-team-4/pull/212
 https://github.com/COSC-499-W2025/capstone-project-team-4/pull/226


## Test Reports
We had done manual testing and used unit testing. 

<img width="595" height="645" alt="image" src="https://github.com/user-attachments/assets/f0e13981-10c6-49c1-8ffb-a14b5adb9310" />

