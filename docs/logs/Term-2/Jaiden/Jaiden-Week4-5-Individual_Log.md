# Week 4-5 (Jan 25 - Feb 8) Individual Log 

## Overview

These past 2 weeks, I was working on two of the features within the requirements. The two features are the feature to include nested zip files 
(the requirement regarding one zip with multiple projects) and a feature that recognizes duplicate files maintaining only one within the system.
The duplicate files requirement was sort of vague as we don't store any of the uploaded files on the system, as a result I made it hash through 
all files in the project to return a key, if the file uploaded is identical to a previous one, it will return the previous analysis result 
making it faster when analyzing identical projects. 

## Coding Tasks
<img width="853" height="503" alt="image" src="https://github.com/user-attachments/assets/f1be41eb-c56f-4b0a-a07e-01d4cc3edebe" />

## PR links
[PR 178](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/178) - Nested Projects in ZIP

[PR 189](https://github.com/COSC-499-W2025/capstone-project-team-4/pull/189) - Duplicate Files in System

## Connection to previous weeks 
These two weeks work connect to previous weeks in many ways, the system previously supported basic ZIP analysis with single projects. These
two weeks built upon that with improved project submission handling addressing the duplicate uploads and nested zip files as per the requirements 
for Milestone #2. 

## Testing/Debugging tasks
In previous weeks we had neglected testing in our features, now we have starting using unit testing again in pytest, I have wrote and debugged 
my code through several tests which all pass. Both features have instructions on manual testing and automatic testing.

## Review/Collaboration Tasks 
> Reviewed: PR #183, #184, #185, #188 

## Plans/Goals for Next Week
Continue working on Milestone requirements and refactor aspects of PR 189 to read files faster (hashing before unzipping) 
