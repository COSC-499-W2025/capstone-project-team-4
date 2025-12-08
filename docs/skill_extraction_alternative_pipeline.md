# Skill Extraction - Alternative Analysis Pipeline

## Core Objectives
- **Identify Language & Framework:** Determine the primary programming language(s) and accompanying frameworks/libraries.

- **Map Artifacts to Skills:** Associate specific file extensions, directory names, and source code keywords with high-level technical skills (e.g., OOP, REST API Development).

- **Calculate Confidence:** Use a weighted scoring system (Phase 2 implementation) based on frequency and context to generate a robust confidence score for each extracted skill.

## Extraction Pipeline

### 1. Initialization & Language Identification

| **Step** | **Description** | **Artifact Analysis** | **Status** |
|-----------|-----------------|-----------------------|-----------|
| 1.1 Project Scan | Recursively lists all files and directories in the repository. | All files/folders. | Completed |
| 1.2 Programming Language Identification | Primary language is determined by counting common file extensions. Secondary languages are also noted. | .java, .py, .js, .ts, .cs, .go, etc. | In-Progress |
| 1.3 Framework Identification | Key dependency files are checked to identify frameworks and major libraries. | package.json, pom.xml, requirements.txt, build.gradle, Gemfile | In-Progress |

### 2. Structural Analysis

| **Step** | **Description** | **Artifact Analysis** | **Status** |
|-----------|-----------------|-----------------------|-----------|
| 2.1 Directory Mapping | Directories are checked against a predefined list of structure indicators. | tests/, models/, controllers/, services/, client/, server/, docs/, migrations/ | |
| 2.2 Deployment Artificants | Presence of specific configuration files indicates DevOps or Cloud skills. | Dockerfile, docker-compose.yml, Jenkinsfile, .yaml files (for Kubernetes). | |

### 3. Code Content Anlysis

| **Step** | **Description** | **Artifact Analysis** | **Status** |
|-----------|-----------------|-----------------------|-----------|
| 3.1 Keyword Counting | Language-specific files are tokenized and scanned for high-value keywords (e.g., class, SELECT, async) and frequency is counted. | Source code | |
| 3.2 Contextual Anlysis | Keywords are scored based on proximity or usage. (e.g., new followed by a class name strengthens the OOP score). | Source code | |

## Weighted Skill Confidence Scoring System

The Confidence Score (CS) for any extracted skill is calculated by combining weighted scores from three distinct pipeline stages: Structural Evidence, Content Frequency, and Contextual Strength.

CS_skill = min(1.0, W_Structural + W_Content + W_Context)

| **Score Component** | **Pipeline Stage** | **Maximum Weight** | **Purpose**|
|-----------|-----------|-----------|-----------|
|W_Structural| Stage 2 (Architecture) | 0.45 | Proves the Intent and setup for the skill.|
|W_Content| Stage 3.1 (Keyword Counting)| 0.60| Proves the Execution Frequency of core concepts.|
|W_Context|Stage 3.2 (Contextual Analysis)| 0.25 | Proves the Quality and specific application of the skill.|
|Total Max Score| | 1.30 | The cap at 1.0 ensures a perfect score for overwhelming evidence.|

### W_Structural - Structural Evidence Score (Max 0.45)

This score is based on the mere presence of key files and directories, indicating a clear architectural intention to use the skill.

|**Evidence Type**| **Weight**| **Justification**| **Artifact Example**|
|----------|----------|----------|----------|
| High-Commitment Files| 0.30 | **Highest Intent:** Dedicated Configuration Files (e.g., Dockerfile, Jenkinsfile) are an explicit commitment to a specific methodology (e.g., DevOps/Containerization).| Dockerfile, pom.xml (with a specific testing library).|
|Architectural Folders| 0.10 | **Design Intent:** Consistent folder structures (models/, tests/, routes/) indicate adherence to a known design pattern (e.g., MVC, TDD).|Presence of controllers/, migrations/, __tests__/ directories.|
|Documentation Mention| 0.05 | Low-Level Intent: Explicitly stating a skill in the documentation (README.md) is weak evidence but contributes to the base score.| Explicitly mentions "Microservice" or "TDD" in the README.md.|

### W_Content - Content Frequency Score (Max 0.60)

This is the largest component, relying on the density of core skill-related keywords in the code. Scores are based on Normalized Frequency (NF) to reward high keyword usage regardless of total project size.

Normalized Frequency (NF) = Total Keyword Count / Total Project Lines of Code (LOC)

|**Keyword Type**| **Weight per Skill Category**| **Justification**| **Normalized Frequency Thresholds(NFT)**|
|----------|----------|----------|----------|
|High-Skill Keywords| 0.10 | Skill Core: Keywords essential to the skill (e.g., class, SELECT, async).| NFT1: 0.001 (Low Density) NFT2: 0.005 (Medium Density) NFT3: 0.010 (High Density)|
|Low-Skill Keywords| 0.05 | Skill Support: Necessary but less defining syntax (e.g., private, this, WHERE).| NFT1: 0.0005 (Medium Density) NFT2: 0.0010 (High Density)|

### W_Context - Contextual Strength Score (Max 0.25)

This score assesses the quality and correct application of the skill by identifying complex or multi-keyword patterns, providing stronger evidence than raw frequency alone.

| Evidence Type               | Weight (w) | Justification                                                                                  | Pattern/Condition for Triggering                                                                 |
|-----------------------------|------------|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Complex Patterns/Syntax     | 0.10       | Proof of Concept: Specific, advanced syntax that proves a deeper understanding (e.g., implementing Inheritance). | Pattern Match: `class X extends Y` or `router.get('/', ...)` found ≥5 times.                   |
| Safety/Robustness Logic     | 0.10       | Quality Indicator: Consistent use of defensive programming around critical operations, proving reliability skill. | Consistent use of `try-catch/finally` blocks around I/O, database, or network calls.          |
| Active Library Usage        | 0.05       | Application Density: Confirms that imported libraries are actively used and not just listed as dependencies. | Library-specific function calls (e.g., `np.array`, `plt.show` for Data Science) found across multiple files. |

### Confidence Score Tiers (Interpretation)

Once the score is calculated, it can be mapped to an easily understood tier for resume builder use.

| Score Range  | Interpretation           | Use                                         |
|-------------|--------------------------|------------------------------------------------------------|
| 0.0 - 0.15  | Minimal Exposure         | Do not list the skill.                                     |
| 0.16 - 0.40 | Basic Familiarity        | List as "Familiar with..."                                 |
| 0.41 - 0.65 | Competent/Applied        | List as "Competent in..." (Solid evidence).               |
| 0.66 - 0.85 | Proficient/Strong        | List as "Proficient in..." (Clear, consistent evidence).  |
| 0.86 - 1.00 | Expert/Extensive         | List as "Expert in..." (Overwhelming evidence across all stages). |
