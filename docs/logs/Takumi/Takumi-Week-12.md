# **Week 12 Individual Log**
This week I’ve worked on improving our library detection system using Tree-sitter, setting up the GitHub API skill extraction, and fixing environment issues related to Python versions and dependencies.

<img width="762" height="537" alt="Screenshot 2025-11-23 at 22 30 40" src="https://github.com/user-attachments/assets/dcf99473-4226-4d55-9f52-ec789d291a75" />



## **Tasks Completed:**
- Worked on library detection using both recursive scanning and Tree-sitter, comparing which method gives more accurate import extraction.
- Implemented initial version of GitHub API skill extraction, including extracting basic metrics (e.g., number of commits per user).
- Set up and tested the environment to ensure Tree-sitter works with our code analysis pipeline.
- Generated JSON outputs for complexity analysis and verified output formatting.
- Troubleshot venv issues (Python version conflicts, dependency installation problems).
- Discussed with teammates how these features fit into our project scope (likely “plus-alpha” features).


## **Plan/to-dos for next cycle** 
- Finalize the library detection module using Tree-sitter as the main parsing method.
- Improve the GitHub skill extraction to include more metrics (e.g., PR count, issue activity, languages used).
- Integrate library detection + complexity analysis into a unified report.
- Clean up CLI outputs to follow team formatting conventions.
- Add missing docs and comments to new modules.
- Confirm which features are required for Milestone 2 vs. optional additions.
