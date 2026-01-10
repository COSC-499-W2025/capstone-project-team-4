# Resume Builder Pipeline
This document outlines a 5-stage pipeline that transforms repository analysis outputs into a resume that can then be edited visually in a canvas-like interface.

---

## Stage 1: User Profile

**Goal:** Capture who the resume is about (the human), independent of any particular project.

### Responsibilities

- Collect and store user-specific information:
  - **Identity:** name, preferred display name, pronouns (optional)
  - **Professional label:** title (e.g., “Software Engineer | Data-Driven Developer”)
  - **Contact info:** email, phone, location
  - **Online presence:** GitHub, LinkedIn, portfolio, personal site
  - **Summary:** 2–4 sentence professional summary or objective
- Provide a **stable JSON format** that other stages can rely on.

### Data Structure

File: `user_profile.json`

```json
{
  "name": "Kussh Satija",
  "title": "Software Engineer | Data-Driven Developer",
  "location": "Kelowna, BC, Canada",
  "email": "kussh@example.com",
  "phone": "+1 (555) 555-5555",
  "links": {
    "github": "https://github.com/your-handle",
    "linkedin": "https://linkedin.com/in/your-handle",
    "portfolio": "https://your-portfolio.com"
  },
  "summary": "Software engineer who builds tools that analyze repositories for skills, complexity, and collaboration metrics to generate data-backed insights."
}
```
## Stage 2: Build Raw Resume Data
**Goal:** Create a single raw resume data object that combines:
- The user profile (Stage 1) and,
- The analysis outputs (complexity, skills, contributors, metadata)
### Output

- Unified resume data:
  - `outputs/capstone-project-team-4/resume_raw_data.json`

This file contains everything needed for later stages:

- `user` – who the resume is about  
- `project` – what this repository shows about the user  
- `skills` – raw skills extracted from the analysis  
- `contributors` – team-level and user-level contribution stats  
- `meta` – pipeline metadata (paths, timestamps)

### Inputs
1. **User Profile**
   - Fields from `user_profile.json`:
     - `name`, `title`, `location`, `email`, `phone`, `links`, `summary`.

2. **Repository Metadata**
   Shape equivalent to `metadata.json`:
   - `metadata.total_files`, `total_size_bytes`, `average_file_size_bytes`, `duration_days`, `collaborative`
   - `project_root` (path to repo root).

3. **Complexity Analysis**
   Shape equivalent to `complexity.json`:
   - `functions`: list of `{file_path, name, start_line, end_line, cyclomatic_complexity}`.

4. **Contributor Stats**
   Shape equivalent to `contributors.json`:
   - List of entries, each with:
     - `name`, `primary_email`, `commits`, `percent`,
       `total_lines_added`, `total_lines_deleted`, `files_modified`

5. **Curated Skill Extract**
   Shape equivalent to `skill_extract.json`:
   - Category buckets:
     - e.g., `"Web Development"`, `"DevOps & Infrastructure"`, `"Programming Languages"`, `"Other"` each with skill lists.
   - `languages`: list of languages detected (INI, JSON, Java, Markdown, Python, Text, YAML).
   - `frameworks`: list of frameworks (e.g., Docker Compose, FastAPI, Kubernetes, Phoenix).
   - `skills_flat`: one flat list of curated skills (API Documentation, Async Programming, Backend Development, etc.).

6. **Global Skill Statistics**
   Shape equivalent to `skills_extracted.json`:
   - `summary.total_files`, `files_analyzed`, `files_skipped`   
   - `summary.languages_encountered`
   - `summary.global_skill_counts`
   - `skill_activity_heatmap`

### Stage 2 Responsibilities

Stage 2 (e.g. `build_resume_data.py`) must:

1. **Attach the User Profile**
2. **Create a Project Section for that User**
3. **Create a Skills Section (Stats + Curated)**
4. **Create a Contributors Section**
5. **Attach Meta Information**

### Output Template: `resume_raw_data.json`

Below is the **intended shape** of `resume_raw_data.json`
```json
{
  "user": {
    "name": "Kussh Satija",
    "title": "Software Engineer | Data-Driven Developer",
    "location": "Kelowna, BC, Canada",
    "email": "kussh@example.com",
    "phone": "+1 (555) 555-5555",
    "links": {
      "github": "https://github.com/your-handle",
      "linkedin": "https://linkedin.com/in/your-handle",
      "portfolio": "https://your-portfolio.com"
    },
    "summary": "Software engineer who builds tools that analyze repositories for skills, complexity, and collaboration metrics to generate data-backed insights."
  },

  "project": {
    "title": "capstone-project-team-4",          // from resume_item.title
    "project_root": "/Users/kusshsatija/capstone-project-team-4",
    "run_timestamp": "2026-01-08-12-34-56",

    "metadata": {
      "total_files": 93,
      "total_size_bytes": 57188512,
      "average_file_size_bytes": 614930.24,
      "duration_days": 79.85,
      "collaborative": true
    },

    "complexity_summary": {
      "total_functions": 180,                  // example
      "avg_cyclomatic_complexity": 3.9,        // derived from complexity analysis
      "max_cyclomatic_complexity": 68,         // derived from complexity analysis
      "threshold": 5,
      "functions_over_threshold": 12           // example
    },

    "languages": [
      "INI",
      "JSON",
      "Java",
      "Markdown",
      "Python",
      "Text",
      "YAML"
    ],

    "frameworks": [
      "Docker Compose",
      "FastAPI",
      "Kubernetes",
      "Phoenix"
    ],

    "resume_highlights": [
      "• Developed capstone-project-team-4 using API Documentation, Async Programming, Backend Development, Containerization, Docker Compose, FastAPI, INI and JSON.",
      "• Analyzed 93 source files with an average cyclomatic complexity of 3.9 (max 68).",
      "• Owned 15.6% of project contributions with 6,564 lines added, demonstrating feature ownership and collaborative Git workflow."
    ]
  },

  "skills": {
    "languages_encountered": [
      "yaml",
      "json",
      "java",
      "markdown",
      "python"
    ],
    "global_skill_counts": {
      "Core JSON Structure": 102991,
      "JSON Data Types": 102903,
      "Code Blocks & Inline Code": 851,
      "Text Formatting": 593,
      "Exception Handling & Robustness": 486,
      "File I/O & Serialization": 424,
      "Unit Testing & TDD": 368
      // ...
    },
    "skills_ranked": [
      { "name": "Core JSON Structure", "count": 102991 },
      { "name": "JSON Data Types", "count": 102903 },
      { "name": "Code Blocks & Inline Code", "count": 851 },
      { "name": "Text Formatting", "count": 593 },
      { "name": "Exception Handling & Robustness", "count": 486 }
      // ... full sorted list
    ],
    "skill_activity_heatmap": {
      "Unit Testing & TDD": {
        "2025-11-20": 52,
        "2025-11-26": 89
        // ...
      },
      "Exception Handling & Robustness": {
        "2025-11-20": 53
        // ...
      }
      // ... other skills
    }
  },

  "skills_curated": {
    "groups": {
      "Web Development": [
        "API Documentation",
        "RESTful APIs"
      ],
      "DevOps & Infrastructure": [
        "Containerization"
      ],
      "Programming Languages": [
        "Object-Oriented Programming"
      ],
      "Other": [
        "Async Programming",
        "Backend Development",
        "Documentation",
        "Multi-Container Applications",
        "Technical Writing"
      ]
    },
    "languages_reported": [
      "INI",
      "JSON",
      "Java",
      "Markdown",
      "Python",
      "Text",
      "YAML"
    ],
    "frameworks_reported": [
      "Docker Compose",
      "FastAPI",
      "Kubernetes",
      "Phoenix"
    ],
    "skills_flat": [
      "API Documentation",
      "Async Programming",
      "Backend Development",
      "Containerization",
      "Documentation",
      "Multi-Container Applications",
      "Object-Oriented Programming",
      "RESTful APIs",
      "Technical Writing"
    ]
  },

  "contributors": {
    "all": [
      {
        "name": "Slimosaurus",
        "primary_email": "79215781+jaidenlo@users.noreply.github.com",
        "commits": 21,
        "percent": 7.27,
        "total_lines_added": 4848,
        "total_lines_deleted": 2289,
        "files_modified": { "...": 1 },
        "files_touched": 60,
        "top_files": [
          "src/main.py",
          "src/core/aggregate_outputs.py",
          "README.md",
          "requirements.txt",
          "tests/test_app.py"
        ]
      }
      // ... other contributors
    ],

    "current_user": {
      // whichever contributor matches user_profile (by email or name)
      "name": "Kussh Satija",
      "primary_email": "kussh@example.com",
      "commits": 30,
      "percent": 15.6,
      "total_lines_added": 6564,
      "total_lines_deleted": 500,
      "files_modified": {
        "src/core/project_analyzer.py": 4,
        "src/core/resume_skill_extractor.py": 2
        // ...
      },
      "files_touched": 20,
      "top_files": [
        "src/core/project_analyzer.py",
        "src/core/resume_skill_extractor.py",
        "docs/logs/Kussh/Week 4/Week 4 - Log - Kussh.md"
      ]
    }
  },

  "meta": {
    "project_root": "/Users/kusshsatija/capstone-project-team-4",
    "total_files": 93,
    "files_analyzed": 78,
    "files_skipped": 15,
    "run_timestamp": "2026-01-08-12-34-56"
  }
}
```
## Stage 3: Allow User to Choose Skills

**Goal:** Let the user decide which skills from `resume_raw_data.json` should appear on the resume.

**Input:**
- `resume_raw_data.json` (from Stage 2)

**Output:**
- `resume_chosen_skills.json`

**Responsibilities:**
- Read skills extracted.
- Present skills (e.g., top N by count + curated list) in an interactive flow:
  - For each skill: `[Y]es / [n]o / [q]uit` (ENTER = Yes).
- Mark each skill with a `keep` flag and produce:
  - `skills.selected_names`: final list of chosen skills.
- Preserve all original skill stats for later use (counts, heatmap, groups).


## Stage 4: Generate Resume from Template

**Goal:** Render a formatted resume from `resume_chosen_skills.json` using a template engine.

**Input:**
- `resume_chosen_skills.json`
- Template file (e.g., `templates/resume_template.md` using Jinja2)

**Output:**
- `resume.md` (or `.html`, `.pdf`, etc.)

**Responsibilities:**
- Load:
  - `user` (profile/header)
  - `project` (title, highlights, complexity summary, languages/frameworks)
  - `skills.selected_names` (main skills section)
  - `contributors.current_user` (ownership/impact bullets)
- Fill template sections:
  - Header (name, title, contact)
  - Summary
  - Skills
  - Project / Experience
- Write the rendered resume to the target file.


## Stage 5: Implement Canvas Feature for User Editing

**Goal:** Provide a visual editor (“canvas”) for fine-tuning the resume without touching JSON or templates.

**Input:**
- Initial rendered resume (e.g., `resume.md` or HTML)
- Underlying data (`resume_chosen_skills.json`)

**Output:**
- `resume_final.md` / `resume_final.pdf`
- (Optional) Updated structured config for future regenerations

**Responsibilities:**
- Show a live preview of the resume with:
  - Editable text (summary, bullets, headings)
  - Toggles to show/hide sections (skills, project details, etc.)
  - Optional reordering of sections and items.
- Persist edits:
  - Export final formatted resume.
  - Optionally update a JSON/YAML config describing customizations (e.g., hidden sections, custom wording).
