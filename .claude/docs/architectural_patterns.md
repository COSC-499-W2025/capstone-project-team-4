# Architectural Patterns

This document describes the recurring architectural patterns, design decisions, and conventions used throughout the codebase.

## 1. Repository/Data Access Pattern

Centralized database abstraction in `src/core/database.py`. All SQLite operations go through this module.

**Conventions:**
- `get_*()` functions for reads
- `save_*()` functions for writes
- `init_db()` for schema initialization
- Each function creates fresh connections (no pooling)

**References:** `src/core/database.py:15-514`

## 2. Dataclass Pattern

Python dataclasses used for immutable data structures without behavior.

**Usage locations:**
- `src/core/code_complexity.py:198` - `FunctionMetrics`
- `src/core/language_analyzer.py:9,26,40` - `FileStats`, `Constants`, `LanguageConfig`
- `src/core/contribution_ranking.py:14` - `ProjectContributionSummary`
- `src/core/project_summarizer.py:25` - `ProjectSummary`

## 3. Configuration Management Pattern

Dual-layer configuration using JSON files for user preferences and YAML files for static rules.

**Configuration sources (in priority order):**
1. Module-level constants (defaults)
2. YAML files: `src/core/rules/frameworks.yml`, `src/core/rules/language_config.yml`
3. JSON files: `src/data/consent_config.json`
4. SQLite database for persistence

**Reference:** `src/core/config_manager.py:44-55`

## 4. Pipeline/Workflow Orchestration Pattern

Sequential data processing pipeline in `src/main.py`. Each stage transforms data from the previous stage.

**Pipeline stages (in order):**
1. Metadata parsing
2. Git analysis (contributors)
3. Code complexity calculation (tree-sitter AST)
4. Skill extraction
5. Database storage
6. Report generation

**Reference:** `src/main.py:68-200`

## 5. Error Handling Pattern

Functions return tuples `(success: bool, errors: List[str])` instead of raising exceptions. Enables graceful degradation.

**Examples:**
- `src/core/zip_file_validator.py:12-95` - Validation returns error list
- `src/core/framework_detector.py:43-71` - Safe file loading
- `src/core/aggregate_outputs.py:8-33` - Graceful JSON loading

## 6. Mapping/Enumeration Pattern

Declarative dictionaries at module level for lookups without conditional logic.

**Examples:**
- `src/core/code_complexity.py:10-140` - `EXT_TO_LANG`, `LANG_TO_PARSER_NAME`, `LANGUAGE_SPECS`
- `src/core/resume_skill_extractor.py:24-250` - `LANGUAGE_SKILLS`, `FRAMEWORK_SKILLS`
- `src/core/language_analyzer.py:99-119` - `CommentDetector.COMMENT_PATTERNS`
- `src/core/metadata_parser.py:18-91` - `SKIP_DIRECTORIES`, `SKIP_EXTENSIONS`

## 7. Constructor Injection Pattern

Dependencies passed via constructor for testability. No DI framework; manual injection.

**Example from `src/core/language_analyzer.py:196-245`:**
- `FileWalker` takes `LanguageConfig`
- `FileAnalyzer` takes `config`, `comment_detector`, `file_walker`
- `ProjectAnalyzer` composes all above

## 8. Weighted Scoring Pattern

Multi-factor scoring with configurable weights for ranking/prioritization.

**Examples:**
- `src/core/contribution_ranking.py:28-48` - `compute_contribution_score()`
- `src/core/project_summarizer.py:77-150` - Project ranking
- `src/core/resume_item_generator.py:43-100` - Resume generation

## 9. Iterator/Generator Pattern

Memory-efficient file traversal using generators instead of loading full lists.

**Examples:**
- `src/core/language_analyzer.py:164` - `FileWalker.walk_source_files()` returns `Iterator[str]`
- `src/core/framework_detector.py:76-81` - `any_glob()` with `rglob`

## 10. Regex-Based Detection Pattern

Skills and frameworks detected using regex patterns defined in JSON files.

**Examples:**
- `src/core/skill_extractor_java.py:56-73` - Pattern-based skill detection
- `src/core/alternate_skill_extractor.py:41-73` - Fast regex matching
- Skill mappings in `src/data/skill_mapping_*.json` (19 files)

## 11. CLI Command Pattern (Typer)

Commands registered via `@app.command()` decorator. Arguments use `typer.Argument()` and `typer.Option()`.

**Reference:** `src/main.py:55-85`

## 12. Test Fixture Pattern

Pytest fixtures with `monkeypatch` for test isolation. Each test gets temporary directories.

**Examples:**
- `tests/test_config_manager.py:14-78`
- `tests/test_language_analyzer.py:15-100`
- `tests/framework_detection/conftest.py` - Shared fixtures

## Key Design Decisions

### Minimal OOP
Classes used mainly for data containers (dataclasses) or grouping related methods. No deep inheritance hierarchies.

### Functional Style
Pure functions preferred. Immutability emphasized. No global state mutation.

### Database-Centric
All state persisted to SQLite. Raw SQL with parameterized queries (no ORM).

### Error as Data
Errors returned as structured data rather than raised exceptions. Enables graceful degradation.

### Batch Processing
Designed for one-shot analysis runs. No persistent services - reads project, analyzes, saves results, exits.
