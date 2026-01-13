"""
Core analysis modules for the Project Analyzer API.

This module is organized into logical subdirectories:

- analyzers/ - Code analysis (complexity, language, contributor, project_stats)
- extractors/ - Data extraction (metadata, framework, skill)
- generators/ - Output generation (resume)
- validators/ - Input validation (zip)
- utils/ - Shared utilities (logging, file_walker)
- ranking/ - Contribution ranking
- constants.py - Shared constants

Import directly from the appropriate submodule:
    from src.core.analyzers.complexity import analyze_file
    from src.core.extractors.skill import analyze_project_skills
    from src.core.generators.resume import generate_resume_item
"""
