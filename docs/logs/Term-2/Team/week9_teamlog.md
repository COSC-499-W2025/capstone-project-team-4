# Team 4 Term 2 Week 9

## Milestone recapped

This week, we began working on Milestone 3. We distributed tasks from Milestone 3’s requirements so that each team member knew what to work on. After that, we worked on fixing some bugs and improving stability of the system, especially in the upload flow and project summary display. We also finalized authentication for the remaining endpoints to ensure that only authorized users can access or modify certain data. We also implemented login and register page UI so users can create accounts and sign in. We also fixed issues related to how uploaded projects are ordered and displayed to make it easier for users to view and manage their project. We also added account management features, including data privacy settings where users can control data collection preferences. In addition, we implemented a profile editing feature that allows logged-in users to view and update their profile information through the Account page.

## Plan To-Dos for Next Cycle 

- Implementation of a feature allowing users to configure their preferences regarding AI usage and other settings via the UI
- Visualization for some of the analysis (Chronological, comparison charts, etc)
- Integrating snapshot comparison to our frontend

## Burnup chart

<img width="984" height="694" alt="Screenshot 2026-03-08 at 20 39 40" src="https://github.com/user-attachments/assets/2408e0b1-a8c0-4700-a7a3-fb1674d83410" />


## Features Planned for this Milestone

- Fixed bugs and improved the stability of the upload flow and project summary display
- Add/finalized working authentication for the final few endpoints
- Fixed uploaded projects ordering/viewing
- Implemented Login, Register page UI
- Implemented user-profile/me endpoints 
- Implemented Edit Profile 
- Implemented data button under account
- Implements the user-authenticated profile editing feature for the resume builder system

## Project Board Tasks Associated with those Features

- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/242
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/239 
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/240
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/244
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/245
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/247


## Test Reports

For the backend, we mainly used pytest for automated testing as usual, and for the frontend, we mainly used Vitest for automated testing. We also performed manual testing by checking the endpoints through Swagger UI for the backend and verifying on the frontend that the features were working properly.
