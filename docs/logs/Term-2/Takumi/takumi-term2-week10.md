## Week 10 – Individual Log (Takumi)

### Overview
Implemented the snapshot comparison feature on the frontend, connecting it to the existing backend endpoints. Extended the feature to support a user-controlled range slider so users can compare any two points in commit history. Added live commit dates on the slider labels by building a new /commit-timeline backend endpoint. Wrote a full frontend test suite for the modal component.

### Testing and Debugging Tasks
- Wrote 57 tests for `SnapshotComparisonModal`, covering API calls, loading states, error states, collapsible rows, complexity metrics, range slider behaviour, and live timeline dates.
- Debugged a concurrency issue where the `commit-timeline` GET and `compare` GET were consuming each other's mocked responses, causing component crashes. Fixed by switching to URL-routing `mockImplementation` in `beforeEach`.
- Fixed 16 pre-existing failing tests in `Instruction.test.jsx` and `useFileUpload.js` that were blocking the test suite.
- Fixed a backend `AttributeError` caused by calling a non-existent method on `ProjectRepository`, caught at runtime after Docker rebuild.

### Reviewing and Collaboration Tasks
Reviewed:
- [PR#264](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/264)
- [PR#258](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/258)
- [PR#257](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/257)
- [PR#256](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/256)
- [PR#255](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/255)

### Connection to Previous Week
Last week I focused on stabilizing the system by reverting unstable backend changes, fixing frontend crashes, and resolving database issues caused by the disk running out of space. This week I implemented the snapshot comparison modal, connected it to the backend endpoints, and added a range slider with commit dates.

### Plan for Next Week  
Since we are having peer testing this week, we will update/add new features to our system based on user feedback.

### Issues / Blockers
- The branch was switched mid-implementation, reverting completed work and requiring the same features to be re-implemented from scratch.
- Backend files were repeatedly overwritten by accidental saves, requiring the same edits to be re-applied multiple times.
- Docker disk space ran out twice, blocking rebuilds until space was manually freed.
- Concurrent GET calls in tests caused non-obvious component crashes that required significant debugging to diagnose and fix.
