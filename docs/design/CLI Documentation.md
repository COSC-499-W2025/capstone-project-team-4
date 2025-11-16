 # CLI Documentation

## Mining Digital Work Artifacts CLI

### Available Commands

| Command | Description |
|---------|-------------|
| `consent` | Manage user consent and external processing permission |
| `status` | Print current consent and external-usage settings |
| `info` | Show information about the application and available commands |
| `external-permission` | Ask for and log permission to use an external service |
| `extract` | Extract and analyze metadata from ZIP files, directories, or single files |
| `analyze-language` | Analyze programming languages and lines of code in projects |

---

## Command Details

### 1. Consent Management

**Usage:** `python -m src.main consent [OPTIONS]`

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

# Disallow external API usage
python -m src.main consent --no-external

# Combine options
python -m src.main consent --grant --external
```

**Sample Output:**
```
Running in virtual env: True
Database initialized successfully.
Loaded: {'theme': 'dark', 'notifications': True}
Consent granted.

Current configuration:
{'consent_granted': True, 'external_allowed': False, 'external_last_notice_version': 0}
```

---

### 2. Status Check

**Usage:** `python -m src.main status`

**Description:** Prints current consent and external-usage settings in JSON format.

**Example:**
```bash
python -m src.main status
```

---

### 3. Application Information

**Usage:** `python -m src.main info`

**Description:** Shows information about the application and lists all available commands.

**Example:**
```bash
python -m src.main info
```

---

### 4. External Permission Request

**Usage:** `python -m src.main external-permission [SERVICE]`

**Description:** Ask for and log permission to use an external service.

**Example:**
```bash
# Request permission for default API service
python -m src.main external-permission

# Request permission for specific service
python -m src.main external-permission "OpenAI API"
```

---

### 5. Extract and Analyze Metadata

**Usage:** `python -m src.main extract [OPTIONS] PATH`

**Description:** Extract and analyze metadata from ZIP files, directories, or single files. Saves results as `metadata.json` in the output directory.

**Arguments:**
- `PATH` - Path to a ZIP file, directory, or single file (required)

**Options:**
- `--out, -o PATH` - Directory to write outputs (default: ./outputs)
- `--external/--no-external` - Allow or disallow external APIs/services for this run

**Examples:**
```bash
# Extract metadata from a ZIP file
python -m src.main extract project.zip

# Extract metadata from a directory
python -m src.main extract /path/to/project

# Extract metadata from a single file
python -m src.main extract document.pdf

# Specify custom output directory
python -m src.main extract project.zip --out /custom/output/path

# Allow external services for this extraction
python -m src.main extract project.zip --external
```

**Output:** Creates `{filename}_metadata.json` with file information including:
- Filename and path
- File type (MIME type)
- File size
- Creation and modification timestamps
- Processing status and any errors

---

### 6. Language Analysis

**Usage:** `python -m src.main analyze-language [OPTIONS] PATH`

**Description:** Analyze programming languages and lines of code in a project directory or ZIP file. Provides detailed statistics and saves results as JSON.

**Arguments:**
- `PATH` - Path to directory or ZIP file to analyze (required)

**Options:**
- `--unknown` - Show only unknown file types

**Examples:**
```bash
# Analyze a project directory
python -m src.main analyze-language /path/to/project

# Analyze a ZIP file
python -m src.main analyze-language project.zip

# Show only unknown file types
python -m src.main analyze-language /path/to/project --unknown
```

**Sample Output:**
```
📊 Language Analysis for: /path/to/project
============================================================
Language     Files  Total    Code     Comments Blank 
------------------------------------------------------------
Python       15     2,543    2,108    285      150   
JavaScript   8      1,876    1,654    134      88    
TypeScript   5      1,234    1,089    89       56    
HTML         3      456      398      12       46    
CSS          2      234      201      15       18    
YAML         4      123      95       8        20    
------------------------------------------------------------
TOTAL        37     6,466    5,545    

✅ Analysis saved to: ./outputs/project_language_analysis.json
```

**Output Features:**
- Comprehensive language detection (40+ languages supported)
- Lines of code analysis (total, code, comments, blank lines)
- File count statistics
- JSON export for further processing
- Support for both directories and ZIP files
- Intelligent filtering of binary files and build artifacts

---

## Global Options

All commands support these global options:
- `--help` - Show help for the specific command
- `--install-completion` - Install shell completion
- `--show-completion` - Show shell completion script

---

## Configuration Files

The CLI creates and manages configuration files in `src/data/` (ignored by git):
- `config.json` - User preferences and settings
- `config.db` - SQLite database for configuration
- `consent_log.json` - Log of user consent decisions

---

## Output Files

Results are saved to the `outputs/` directory:
- `{name}_metadata.json` - File metadata from extract command
- `{name}_language_analysis.json` - Language analysis results
- Custom output paths can be specified with `--out` option

---

## Requirements

- Python virtual environment
- All dependencies from `requirements.txt`
- User consent must be granted before processing files
- Some features require external API permissions 


