## API Endpoint Documentation

> For more detailed information, check out the Swagger UI documentation at `/docs`.

---

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Creates a new user account. Validates that the email is unique and password is at least 8 characters. |
| POST | `/api/auth/login` | Authenticates a user with email/password via OAuth2 form and returns a token. |
| GET | `/api/auth/me` | Returns the currently authenticated user's data, used to validate tokens. |

---

### Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/analyze/upload` | Upload a ZIP file containing a project. Extracts and analyzes it for languages, frameworks, complexity metrics, and contributor activity, returning a full `AnalysisResult`. |
| POST | `/api/projects/analyze/{project_id}/analyze-libraries-tools` | Re-runs library and tool detection on an already-uploaded project without re-running the full pipeline. |
| POST | `/api/projects/analyze/{project_id}/analyze-frameworks` | Runs targeted framework detection on an existing project using YAML-based rules. |
| POST | `/api/projects/analyze/{project_id}/analyze-tech-stack` | Combines library and framework analysis into a single call for a project. |
| POST | `/api/projects/analyze/{project_id}/contributors/{contributor_id}/analyze-tech-stack` | Narrows tech stack analysis to only files touched by a specific contributor. |
| POST | `/api/projects/analyze/github` | Clones and analyzes a public GitHub repository by URL, with an optional branch parameter. |
| POST | `/api/projects/analyze/directory` | Analyzes a local filesystem directory (intended for development/internal use). |

---

### Portfolio

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/portfolio/generate` | Collects a user's projects, skills, resume highlights, and experiences, then creates a portfolio with a title, summary, and structured content. Saves or updates the portfolio in the database. |
| PUT | `/api/portfolio/{portfolio_id}/edit` | Lets logged-in users update parts of their portfolio such as the title, summary, or content. Returns 403 if the user is not the owner, or 404 if the portfolio does not exist. |
| GET | `/api/portfolio/{portfolio_id}` | Fetches a saved portfolio from the database by ID and returns the full portfolio data (title, summary, and content). |
| PUT | `/api/portfolio/{portfolio_id}/projects/{project_name}/customize` | Adds custom names, descriptions, or URLs to a generated portfolio project. |

---

### Snapshots

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/snapshots/{project_id}/create` | Creates two snapshots in one call: a "current" snapshot (latest state) and a "midpoint" snapshot (halfway through the project's timeline), used to capture progress for later comparison. |
| GET | `/api/snapshots/{project_id}/compare` | Compares the latest current and midpoint snapshots for a project, showing how it has grown or changed over time (e.g. lines of code, complexity, skills added). |
| DELETE | `/api/snapshots/{project_id}/{snapshot_id}` | Deletes a specific snapshot and its associated comparison data. |

---

### Thumbnail

| Method | Path | Description |
|--------|------|-------------|
| PUT | `/api/projects/{project_id}/thumbnail` | Uploads or replaces a project's thumbnail image. If a thumbnail already exists it is safely replaced without creating duplicate records. Returns thumbnail metadata, or 404 if the project does not exist. |
| GET | `/api/projects/{project_id}/thumbnail` | Retrieves the project's thumbnail as a binary image response with the appropriate `Content-Type` header. Supports ETag-based caching (SHA256) via `If-None-Match`. Returns 200 with the image, 304 if unchanged, or 404 if not found. |
| DELETE | `/api/projects/{project_id}/thumbnail` | Safely deletes the thumbnail associated with a project without affecting the project itself. Returns 204 on success or 404 if no thumbnail exists. |

---

### Textual Project Showcase

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/{project_id}/textual-project-showcase` | Returns a structured, portfolio-ready textual summary of a project derived from previously analyzed data. Does not trigger re-analysis, ensuring fast and lightweight retrieval. |

---

### Full Resume

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users/{user_id}/resume` | Aggregates profile, education, experiences, projects, and skills into a single structured resume JSON response. |
| GET | `/api/users/{user_id}/resume/export` | Exports the full resume as a downloadable file in PDF, HTML, or Markdown format. |

---

### User Profiles

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/user-profiles` | Lists all user profiles with pagination. |
| GET | `/api/user-profiles/user/{user_id}` | Returns a specific user's full profile. |
| POST | `/api/user-profiles/user/{user_id}` | Creates a profile for an existing user with personal information fields. |
| PUT | `/api/user-profiles/user/{user_id}` | Partially updates an existing user profile. |
| DELETE | `/api/user-profiles/user/{user_id}` | Deletes a user profile. |

---

## Upload Feature Details

### 1. Nested File Upload

**Endpoint:** `POST /api/projects/analyze/upload`

Uploads and analyzes a project ZIP file. Supports nested ZIP files and can handle multiple projects within a single upload. The system performs analysis on each project independently.

**Request Body** (`multipart/form-data`)

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | The project ZIP file to upload. May contain multiple nested ZIP files. |
| `reuse_cached_analysis` | boolean | If `true`, reuses previous analysis results if the project has been uploaded before. |

**Test Instructions**
1. Upload a ZIP file containing multiple nested projects.
2. Verify that each nested project is processed independently.
3. Upload the same ZIP again with `reuse_cached_analysis=true` and confirm cached results are reused.

**Expected Result:** The system processes nested ZIP files as individual projects and reuses cached results for previously uploaded projects when `reuse_cached_analysis=true`.

---

### 2. Duplicated File Hashing

**Endpoint:** `POST /api/projects/analyze/upload`

Detects and avoids re-analyzing duplicated files by comparing the hash of uploaded files against existing records.

**Request Body** (`multipart/form-data`)

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | The project ZIP file to upload. |
| `reuse_cached_analysis` | boolean | If `true`, reuses prior analysis results for identical files. |

**Test Instructions**
1. Upload a ZIP file containing files that have been previously uploaded.
2. Verify that the system detects duplicate files and reuses prior analysis results based on file hash.
3. Upload a new ZIP with a unique file and confirm that the new file is analyzed fresh.

**Expected Result:** The system detects duplicated files using hashing and reuses analysis results when the same file is uploaded again.

---

### 3. Incremental File Additions

**Endpoint:** `POST /api/projects/analyze/upload`

Handles incremental file additions during project uploads, ensuring that only new or modified files are analyzed on subsequent uploads.

**Request Body** (`multipart/form-data`)

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | The project ZIP file to upload. Only new or modified files will be analyzed. |
| `reuse_cached_analysis` | boolean | If `true`, reuses prior analysis results for unchanged files. |

**Test Instructions**
1. Upload a ZIP file with an initial set of files.
2. Upload the same ZIP again with a small modification or additional files.
3. Verify that only the modified or added files are analyzed, and unchanged files reuse prior results.

**Expected Result:** The system analyzes only new or modified files and avoids reanalyzing unchanged content. Improved performance on subsequent uploads is visible in the console logs.
