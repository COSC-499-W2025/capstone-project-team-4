# Individual Log - Jaiden Lo 
## Weekly Navigation 
[link]

## Connection to Previous Week
In the previous week, the system supported basic ZIP uploads and project analysis. This week builds on that foundation by extending the backend to handle more complex submission scenarios involving multiple projects packaged within nested ZIP files.

## Coding Tasks
- Implemented backend support for analyzing nested ZIP files, enabling the system to recursively detect ZIP archives contained within an uploaded file.
- Added logic to treat each nested ZIP as a separate project, assigning a unique project_id to ensure independent analysis and accurate result reporting.
- Ensured compatibility between nested ZIP processing and the existing project analysis pipeline.
- https://github.com/COSC-499-W2025/capstone-project-team-4/pull/165

## Tests & Debugging 
- Manually tested uploads containing multiple layers of nested ZIP files to confirm all embedded projects were correctly discovered and processed.
- Tested edge cases such as empty ZIPs, and mixed contents to ensure stable behaviors
- Tested using a MAC zip files as they compress it differently and returned errors on initial testing

## Reviewing & Collaboration Tasks
- Discussed integration details with teammates to ensure the nested project IDs aligned with how the frontend displays project summaries.
- Responded to review feedback on PR and made adjustments to imrpvoe clarity of the implementation

## Plans/Goals for Next Week
- Continue finishing tasks from github taskboard
- Respond to feedback and implement changes based on the Peer Review on Monday

