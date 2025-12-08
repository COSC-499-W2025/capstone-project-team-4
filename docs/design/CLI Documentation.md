# CLI Documentation

## Mining Digital Work Artifacts CLI

A comprehensive command-line tool for analyzing GitHub repositories, extracting metadata, tracking contributions, and generating resume-worthy insights from code projects.

### Available Commands

| Command              | Description                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| `analyze-project`    | **Main command** - Full project analysis with metadata, complexity, skills, and resume generation |
| `browse`             | Interactively browse analyzed project outputs                                                     |
| `delete-output`      | Delete specific project analysis outputs                                                          |
| `status`             | Print current consent and configuration settings                                                  |
| `consent`            | Manage user consent and external processing permissions                                           |
| `info`               | Show CLI information and available commands                                                       |
| `summarize`          | Display top-ranked projects with detailed analysis                                                |
| `rank-contributions` | Rank a contributor's impact within a Git project                                                  |
| `rank-projects`      | Show all analyzed projects for a contributor, ranked by contribution score                        |
| `skill-timeline`     | Display chronological timeline of skills used in a project                                        |
| `aggregate-outputs`  | Generate dashboard summary of all analyzed projects                                               |

---

## Command Details

### 1. Analyze Project (Main Command)

**Usage:** `python -m src.main analyze-project [OPTIONS] PATH`

**Description:** Comprehensive project analysis that generates multiple JSON outputs including metadata, code complexity, contributor analysis, skill extraction, and resume items. This is the primary command for full project analysis.

**Arguments:**

- `PATH` - Path to project directory or ZIP file (required)

**Options:**

- `--include-files/--no-include-files` - Include full file list in metadata (default: True)
- `--out, -o PATH` - Output directory (default: ./outputs)

**Examples:**

```bash
# Analyze a project directory
python -m src.main analyze-project /path/to/project

# Analyze a ZIP file
python -m src.main analyze-project project.zip

# Exclude file list from output
python -m src.main analyze-project /path/to/project --no-include-files

# Specify custom output directory
python -m src.main analyze-project project.zip --out /custom/output
```

**Generated Outputs:**
The command creates a timestamped directory with the following JSON files:

- `metadata.json` - Project metadata, file statistics, and file list
- `complexity.json` - Code complexity metrics for functions
- `contributors.json` - Contributor analysis and statistics
- `skill_extract.json` - Extracted skills categorized by type
- `skill_insights.json` - Secondary skill analysis with detailed insights
- `resume_item.json` - Generated resume-worthy project description

**Sample Output:**

```
🎉 Reports generated → ./outputs/my-project/2025-12-07_14-30-45
```

---

### 2. Browse Analyzed Projects

**Usage:** `python -m src.main browse [OPTIONS]`

**Description:** Interactive menu to browse previously analyzed project outputs. Navigate through projects, timestamps, and view JSON files with pretty formatting.

**Options:**

- `--out, -o PATH` - Outputs directory (default: ./outputs)
- `--raw` - Show raw JSON instead of pretty-printed view

**Examples:**

```bash
# Browse default outputs directory
python -m src.main browse

# Browse custom outputs directory
python -m src.main browse --out /custom/outputs

# View raw JSON without formatting
python -m src.main browse --raw
```

**Interactive Flow:**

1. Select a project from the list
2. Select a timestamp (analysis run)
3. Select a JSON file to view
4. View formatted or raw JSON output

---

### 3. Delete Project Outputs

**Usage:** `python -m src.main delete-output [OPTIONS]`

**Description:** Interactively select and delete specific project analysis outputs. Useful for cleaning up old or unwanted analysis results.

**Options:**

- `--out, -o PATH` - Outputs directory (default: ./outputs)

**Examples:**

```bash
# Delete from default outputs directory
python -m src.main delete-output

# Delete from custom outputs directory
python -m src.main delete-output --out /custom/outputs
```

**Interactive Flow:**

1. Select a project
2. Select a timestamp to delete
3. Confirm deletion by typing 'yes'

---

### 4. Status Check

**Usage:** `python -m src.main status`

**Description:** Display current configuration settings including consent status and external API permissions.

**Example:**

```bash
python -m src.main status
```

**Sample Output:**

```json
{
  "consent_granted": true,
  "external_allowed": false,
  "external_last_notice_version": 0
}
```

---

### 5. Consent Management

**Usage:** `python -m src.main consent [OPTIONS]`

**Description:** Manage user consent for data processing and external API usage. Required before running analysis commands.

**Options:**

- `--grant` - Grant consent to process files
- `--revoke` - Revoke consent
- `--external` - Allow use of external APIs/services
- `--no-external` - Disallow use of external APIs/services

**Examples:**

```bash
# Grant consent to process files
python -m src.main consent --grant

# Revoke consent
python -m src.main consent --revoke

# Allow external API usage
python -m src.main consent --external

# Combine options
python -m src.main consent --grant --external
```

**Sample Output:**

```
Consent granted.
External allowed = True

Current configuration:
{'consent_granted': True, 'external_allowed': True, 'external_last_notice_version': 0}
```

---

### 6. Application Information

**Usage:** `python -m src.main info`

**Description:** Display CLI information and a complete list of available commands with descriptions.

**Example:**

```bash
python -m src.main info
```

---

### 7. Summarize Projects

**Usage:** `python -m src.main summarize [OPTIONS]`

**Description:** Display top-ranked analyzed projects with detailed metrics and insights.

**Options:**

- `--sort, -s` - Sort criteria: `complexity`, `contributions`, `skills`, `lines_of_code`, `file_count`, `recent`, `comprehensive` (default: comprehensive)
- `--limit, -l` - Number of projects to show (default: 10)

**Examples:**

```bash
# Show top 10 projects with comprehensive ranking
python -m src.main summarize

# Show top 5 most complex projects
python -m src.main summarize --sort complexity --limit 5

# Show top 20 projects by lines of code
python -m src.main summarize --sort lines_of_code --limit 20

# Show most recently analyzed projects
python -m src.main summarize --sort recent
```

---

### 8. Rank Contributions

**Usage:** `python -m src.main rank-contributions [OPTIONS] PROJECT`

**Description:** Analyze and rank a specific contributor's impact within a Git project based on commits, lines changed, and files touched.

**Arguments:**

- `PROJECT` - Path to Git project directory (required)

**Options:**

- `--name NAME` - Contributor name (required if --email not provided)
- `--email EMAIL` - Contributor email (required if --name not provided)

**Examples:**

```bash
# Rank contributions by name
python -m src.main rank-contributions /path/to/project --name "John Doe"

# Rank contributions by email
python -m src.main rank-contributions /path/to/project --email "john@example.com"
```

**Sample Output:**

```
Contribution Summary
-----------------------
Project: my-project
Commits: 45
Lines Added: 2,345
Lines Deleted: 1,234
Files Touched: 67
Contribution Score: 87.5
```

---

### 9. Rank Projects

**Usage:** `python -m src.main rank-projects [OPTIONS]`

**Description:** Display all analyzed projects for a contributor, ranked by contribution score based on the saved contribution log.

**Options:**

- `--name NAME` - Contributor name (required if --email not provided)
- `--email EMAIL` - Contributor email (required if --name not provided)
- `--top-n N` - Show only top N projects

**Examples:**

```bash
# Show all projects for contributor by name
python -m src.main rank-projects --name "John Doe"

# Show all projects by email
python -m src.main rank-projects --email "john@example.com"

# Show top 5 projects
python -m src.main rank-projects --name "John Doe" --top-n 5
```

**Sample Output:**

```
Projects ranked by contribution score:

1. project-alpha
   Score: 95.50 | Commits: 123 | Lines changed: +4567/-2345 (total 6912) | Files touched: 89

2. project-beta
   Score: 87.25 | Commits: 98 | Lines changed: +3456/-1234 (total 4690) | Files touched: 56
```

---

### 10. Skill Timeline

**Usage:** `python -m src.main skill-timeline PROJECT_PATH`

**Description:** Display a chronological timeline of skills exercised in the most recent analysis of a project.

**Arguments:**

- `PROJECT_PATH` - Path to project directory or folder name in outputs (required)

**Examples:**

```bash
# View skill timeline for a project
python -m src.main skill-timeline /path/to/project

# View skill timeline using folder name
python -m src.main skill-timeline my-project
```

**Sample Output:**

```
📌 Skill Timeline (Chronological)

📅 2025-01-15
   - Python (15)
   - REST API Design (8)
   - Database Management (5)

📅 2025-02-20
   - JavaScript (22)
   - React (18)
   - CSS (12)
```

---

### 11. Aggregate Outputs

**Usage:** `python -m src.main aggregate-outputs [OPTIONS] [OUTPUTS]`

**Description:** Generate a comprehensive dashboard summary of all analyzed projects with statistics and insights.

**Arguments:**

- `OUTPUTS` - Path to outputs directory (default: ./outputs)

**Options:**

- `--json` - Output in JSON format instead of Markdown
- `--out, -o PATH` - Save output to file instead of printing to console

**Examples:**

```bash
# Generate markdown summary
python -m src.main aggregate-outputs

# Generate JSON summary
python -m src.main aggregate-outputs --json

# Save to file
python -m src.main aggregate-outputs --out dashboard.md

# Aggregate custom outputs directory
python -m src.main aggregate-outputs /custom/outputs --out report.md
```

**Output:** Provides aggregated statistics including:

- Total projects analyzed
- Programming languages used across all projects
- Frameworks and technologies detected
- Total lines of code analyzed
- Top contributors across projects

---

## Global Options

All commands support these global options:

- `--help` - Show help for the specific command
- `--install-completion` - Install shell completion
- `--show-completion` - Show shell completion script

---

## Database & Storage

### SQLite Database

The CLI uses a SQLite database to store:

- Project metadata and analysis results
- File information and statistics
- Code complexity metrics
- Contributor data
- Skill extraction results
- Resume items
- Contribution logs

### Output Directory Structure

```
outputs/
├── project-name/
│   ├── 2025-12-07_14-30-45/
│   │   ├── metadata.json
│   │   ├── complexity.json
│   │   ├── contributors.json
│   │   ├── skill_extract.json
│   │   ├── skill_insights.json
│   │   └── resume_item.json
│   └── 2025-12-08_10-15-20/
│       └── ...
└── another-project/
    └── ...
```

---

## Configuration Files

The CLI creates and manages configuration files in `src/data/`:

- `config.json` - User preferences and settings
- `config.db` - SQLite database for all analysis data
- `consent_log.json` - Log of user consent decisions
- `project_contributions_log.json` - Contribution tracking across projects

---

## Output File Descriptions

### metadata.json

Contains comprehensive project metadata:

- Project statistics (file counts, total size, languages used)
- File list with paths, types, sizes, and timestamps
- Project root directory information

### complexity.json

Code complexity analysis:

- Function-level complexity metrics
- Cyclomatic complexity scores
- Maintainability indicators

### contributors.json

Git contributor analysis:

- Commit counts per contributor
- Lines added/deleted per contributor
- Files touched by each contributor
- Contribution percentages

### skill_extract.json

Extracted technical skills:

- Detected programming languages
- Identified frameworks and libraries
- Categorized skills by type
- Proficiency assessments

### skill_insights.json

Secondary skill analysis:

- Detailed skill patterns
- Technology stack insights
- Advanced skill mappings

### resume_item.json

Generated resume-worthy project description:

- Professional project summary
- Key technologies and achievements
- Contribution highlights
- Quantified impact metrics

---

## Requirements

### System Requirements

- Python 3.11.0 or higher
- Git (for contribution analysis)
- 100MB+ free disk space for database and outputs

### Setup Requirements

- Python virtual environment (recommended)
- All dependencies from `requirements.txt`
- User consent must be granted before processing files

### Optional Requirements

- Docker & Docker Compose (for containerized deployment)
- External API keys (if using external services)

---

## Best Practices

1. **Grant Consent First**: Always run `python -m src.main consent --grant` before analysis
2. **Use Virtual Environment**: Activate your virtual environment before running commands
3. **Regular Cleanup**: Use `delete-output` to remove old analysis results
4. **Consistent Naming**: Use consistent contributor names/emails across commands for accurate tracking
5. **Review Outputs**: Use `browse` command to review analysis results interactively
6. **Aggregate Insights**: Run `aggregate-outputs` periodically to generate summary dashboards

---

## Troubleshooting

### Common Issues

**"Consent not granted" error:**

```bash
python -m src.main consent --grant
```

**"outputs folder not found" error:**

```bash
# Create the outputs directory
mkdir outputs
```

**Database errors:**

```bash
# The database is automatically initialized on first run
# If issues persist, delete src/data/config.db and restart
```

**Git repository not found:**

```bash
# Ensure the project directory contains a .git folder
# For rank-contributions command
```

---

## Examples Workflow

### Complete Analysis Workflow

```bash
# 1. Grant consent
python -m src.main consent --grant

# 2. Analyze a project
python -m src.main analyze-project /path/to/project

# 3. Browse results
python -m src.main browse

# 4. Rank contributions
python -m src.main rank-contributions /path/to/project --name "Your Name"

# 5. View all your projects
python -m src.main rank-projects --name "Your Name"

# 6. Generate summary dashboard
python -m src.main aggregate-outputs --out dashboard.md
```

### Quick Analysis

```bash
# One-command full analysis
python -m src.main analyze-project my-project.zip
```

### Contributor Portfolio

```bash
# Analyze multiple projects
python -m src.main analyze-project project1/
python -m src.main analyze-project project2/
python -m src.main analyze-project project3/

# Generate ranked portfolio
python -m src.main rank-projects --name "Your Name"
python -m src.main summarize --sort contributions
```
