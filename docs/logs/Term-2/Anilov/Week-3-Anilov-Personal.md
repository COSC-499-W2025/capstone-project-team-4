# Week 3 - January 18-25 2026

## Overview
This week, I focused on setting up the frontend by installing the necessary packages. Additionally, I created a custom React component for adding and dropping project files for users.

## Coding Tasks
<img width="1176" height="695" alt="image" src="https://github.com/user-attachments/assets/e3a9e1fa-7733-4b69-8198-3aa1a347518e" />

### Dropzone Backend Connection
[PR 151](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/151)

**Closed and migrated changes over to [PR 149](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/149)**

- Add working connection from frontend to backend
- Add `Delete All` button to allow for better flexibility

### Database Migration
[PR 164](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/164)

- Migrate current database (SQLite) into (PostgreSQL)
- Change dependencies and refactored a few files to make it more clean and readable

## Review/Collaboration Tasks
- Reviewed: 
    - [PR 149](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/149)


## Connection to Previous Week
Last week was the creation of the dropzone component where users could drag and drop files. This week, I finally got the successful connection from the frontend to the backend!

## Blockers and Solutions

- **Issue**: Main issue was transitioning from SQLite to PostgreSQL
- **Solution**: Had to use environment variables and changing `settings.py` in case some group members didn't have a connection string that worked.

## Plan for Next Week

- Help out more with the backend now that the frontend is essentially done.
