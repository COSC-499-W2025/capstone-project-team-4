# Week 2 - January 12-18 2026

## Overview
This week, I focused on implementing frontend for the Login and Signup Page. Additionally, I have also been working on the resume builder pipeline that will be used in a later stage to implement a resume builder template. 

## Coding Tasks

- Implemented frontend for Login and Signup page
- Refactored layout into reusable components (e.g., Auth shell, form sections) and aligned imports with the @/components/... alias pattern.
- Extended the test environment with @testing-library/jest-dom matchers and browser API mocks (e.g., ResizeObserver) to support Radix/shadcn components and prevent test failures in JSDOM.
- Added application-level setup to support routing and consistent app bootstrapping, ensuring all pages (Home, Login, Signup) render under a unified root without breaking existing structure.

## Testing and Debugging Tasks

- Added Vitest test suites for Login and Signup pages and accessibility checks.
- Debugged test failures by fixing heading semantics, label collisions, and stabilizing the test environment (cleanup hooks, Radix/ResizeObserver support).
- Achieved successful runs on all tests. 

## Review/Collaboration Tasks
- Reviewed:
  - https://github.com/COSC-499-W2025/capstone-project-team-4/pull/140
  - https://github.com/COSC-499-W2025/capstone-project-team-4/pull/138
  - https://github.com/COSC-499-W2025/capstone-project-team-4/pull/135

## My PR: https://github.com/COSC-499-W2025/capstone-project-team-4/pull/144

## Connection to Previous Week
We spent last week getting everyone synced up with the current codebase and functionality. Once the system was fully integrated, we divided the remaining tasks among the team based on member preference.

## Blockers and Solutions
- **Issue:** Tests involving shadcn/Radix-based components were failing in Vitest because JSDOM does not natively support certain browser APIs (e.g., ResizeObserver) and lacked extended DOM matchers, causing false negatives despite correct UI behavior.
- **Solution:** Enhanced the testing environment by extending @testing-library/jest-dom matchers and adding required browser API mocks (such as ResizeObserver) in setup.js, ensuring Radix components render correctly and tests reliably reflect real browser behavior.

- **Issue:** there was no structured way to navigate between Home, Login, and Signup views, leading to fragile imports and page-level rendering logic that did not scale.
- **Solution:** Added react-router-dom
  
## Plan for Next Week

- Help backend team implement form functionality
- Update UI to be more responsive and follow usabilty principles
- Continue working on resume-builder-template pipeline
- Implement "Account Settings" frontend
