# Week 9 (March 1 2026 - March 8 2026)

## Overview

For this week, I was working on creating and finalizing the video demo for submission.
Additionally, I also finalized adding the auth end points and the appropriate tests as well.
Because of that, I found broken/outdated API endpoints so I had to fix that.

## Coding Tasks
<img width="1492" height="734" alt="T2-Week-9-Log" src="https://github.com/user-attachments/assets/f7e3044f-1b6a-4ac4-85c5-70f7c6872a99" />

### Finalizing Auth for API Endpoints
[Issue 230](https://github.com/COSC-499-W2025/capstone-project-team-4/issues/230)

- Add auth checking for the following endpoints:
 ```
GET /users/{user_id}/resume
GET /users/{user_id}/resume/export
GET /user-profiles/user/{user_id}
POST /user-profiles/user/{user_id}
PUT /user-profiles/user/{user_id}
DELETE /user-profiles/user/{user_id}
GET /user-profiles/{user_id}/experiences
POST /user-profiles/{user_id}/experiences
PUT /user-profiles/{user_id}/experiences/{experience_id}
DELETE /user-profiles/{user_id}/experiences/{experience_id}
GET /privacy-settings/{user_id}
PUT /privacy-settings/{user_id}
```
- **Note:** All it does is prevent the user from accessing the endpoints if they're not logged in/authorized.

## Blockers and Solutions

- **Issue**: Main issue was that some existing endpoints were using outdated function names, etc.
- **Solution**: Just had to use the updated function names in the services!

## Plan for Next Week

- Now that the authentication (and the backend) is done, I need to work more on the frontend!
