# Week 2 - January 12-18 2026

## Overview
This week, I focused on setting up the frontend by installing the necessary packages. Additionally, I created a custom React component for adding and dropping project files for users.

## Coding Tasks

### Frontend Setup
[PR 136](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/136)

- Added packages such as React and Tailwind (plus shadcn) for frontend setup
- Change frontend folder structure to make it more organized

### Custom Dropzone Component
[PR 140](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/140)

- Using React, added a custom component for dragging and dropping project files for users to use.
- Displays the files that were imported. Additionally, gives the user the option to remove individual files.

## Testing and Debugging Tasks

### Testing Dropzone Component
- Utilized vitest for testing the Dropzone component.
- Used mocking to simulate real-world usage.

### Test Coverage
[PR 140](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/140)

- Test coverage includes:
  - Same `title` prop testing
  - Checking to see if the file exists in the list and was uploaded successfully
  - Finds that a file no longer exists once deleted
- Achieved 100% pass rate on 3 tests

## Review/Collaboration Tasks
- Reviewed: 
    - [PR 135](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/135)
    - [PR 138](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/138)

## Connection to Previous Week
Last week was mainly getting up to date with our current functionality and dividing tasks based on what each member wanted to do. So there was no real connection from last week.

## Blockers and Solutions

- **Issue**: Vitest kept failing when trying to test the custom component.
- **Solution**: Turns out I had to do mocking in order to make the tests pass.

## Plan for Next Week

- Integrate the file dropzone to communicate with the backend somewhat (even a simple print statement) to check if backend functionality works fine.
- Figure out what the backend team is doing to integrate the Dropzone functionality well!
