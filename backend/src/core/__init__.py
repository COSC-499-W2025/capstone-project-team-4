"""
Core analysis modules for the Project Analyzer API.

This module is organized into logical subdirectories:

- analyzers/ - Code analysis metrics (complexity, contributor, project_stats)
- detectors/ - Technology detection (language, framework, library, tool, skill, metadata)
- generators/ - Output generation (resume)
- validators/ - Input validation (zip, cross_validator)
- utils/ - Shared utilities (logging, file_walker)
- ranking/ - Contribution ranking
- constants.py - Shared constants

Import directly from the appropriate submodule:
    from src.core.analyzers.complexity import analyze_file
    from src.core.detectors.skill import analyze_project_skills
    from src.core.generators.resume import generate_resume_item
"""
