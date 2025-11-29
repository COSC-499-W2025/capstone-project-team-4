import sqlite3
from pathlib import Path

# Path to DB = /outputs/workmine.db (shared across whole project)
DB_PATH = (
    Path(__file__).resolve().parents[2]  # from src/core → src → project root
    / "outputs"
    / "workmine.db"
)


# -------------------------------------------------
# Connection helper
# -------------------------------------------------
def get_connection():
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))


# -------------------------------------------------
# Initialize DB + ALL tables
# -------------------------------------------------
def init_db():
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Skills (legacy)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_path TEXT NOT NULL,
            skill TEXT NOT NULL
        )
    """)

    # Config
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Projects
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            root TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # File metadata
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            file_size INTEGER,
            created_timestamp INTEGER,
            last_modified INTEGER,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Code complexity
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complexity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            function_name TEXT NOT NULL,
            start_line INTEGER,
            end_line INTEGER,
            cyclomatic_complexity INTEGER,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Contributors
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contributors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT,
            email TEXT,
            commits INTEGER,
            percent REAL,
            total_lines_added INTEGER,
            total_lines_deleted INTEGER,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Contributor → file modification breakdown
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contributor_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contributor_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            modifications INTEGER NOT NULL,
            FOREIGN KEY(contributor_id) REFERENCES contributors(id) ON DELETE CASCADE
        )
    """)

    # Resume-ready skills
    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            category TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Résumé item (one title per project)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Résumé highlights — unlimited + ordered
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_highlights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_item_id INTEGER NOT NULL,
            highlight TEXT NOT NULL,
            highlight_index INTEGER NOT NULL,
            FOREIGN KEY(resume_item_id) REFERENCES resume_items(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


# -------------------------------------------------
# Save project (returns project_id)
# -------------------------------------------------
def save_project(name: str, root: str, timestamp: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name, root, timestamp) VALUES (?, ?, ?)",
        (name, root, timestamp),
    )
    project_id = cur.lastrowid
    conn.commit()
    conn.close()
    return project_id


# -------------------------------------------------
# Save project metadata
# -------------------------------------------------
def save_files(project_id, file_list):
    conn = get_connection()
    cur = conn.cursor()
    for f in file_list:
        cur.execute("""
            INSERT INTO files (
                project_id, path, file_size, created_timestamp, last_modified
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_id,
            f.get("path"),
            f.get("file_size"),
            f.get("created_timestamp"),
            f.get("last_modified"),
        ))
    conn.commit()
    conn.close()


def save_complexity(project_id: int, functions: list[dict]):
    conn = get_connection()
    cur = conn.cursor()
    for fn in functions:
        cur.execute("""
            INSERT INTO complexity (
                project_id, file_path, function_name,
                start_line, end_line, cyclomatic_complexity
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            fn["file_path"],
            fn["name"],
            fn["start_line"],
            fn["end_line"],
            fn["cyclomatic_complexity"],
        ))
    conn.commit()
    conn.close()


def save_contributors(project_id: int, contributors: list[dict]):
    conn = get_connection()
    cur = conn.cursor()
    for c in contributors:
        cur.execute("""
            INSERT INTO contributors (
                project_id, name, email, commits, percent,
                total_lines_added, total_lines_deleted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            c.get("name"),
            c.get("primary_email"),
            c.get("commits"),
            c.get("percent"),
            c.get("total_lines_added"),
            c.get("total_lines_deleted"),
        ))
        cid = cur.lastrowid
        for filename, count in c.get("files_modified", {}).items():
            cur.execute("""
                INSERT INTO contributor_files (contributor_id, filename, modifications)
                VALUES (?, ?, ?)
            """, (cid, filename, count))
    conn.commit()
    conn.close()


# -------------------------------------------------
# Save resume skills
# -------------------------------------------------
def save_resume_skills(project_id: int, skills_by_category: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM project_skills WHERE project_id = ?", (project_id,))
    for category, skill_list in skills_by_category.items():
        for skill in skill_list:
            cur.execute("""
                INSERT INTO project_skills (project_id, skill, category)
                VALUES (?, ?, ?)
            """, (project_id, skill, category))
    conn.commit()
    conn.close()


# -------------------------------------------------
# Save résumé item (title + unlimited highlights)
# -------------------------------------------------
def save_resume_item(project_id: int, resume_item: dict):
    """
    resume_item format example:
    {
        "title": "Software Developer — Capstone",
        "highlights": ["...", "...", ...]
    }
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM resume_items WHERE project_id = ?", (project_id,))
    cur.execute(
        "INSERT INTO resume_items (project_id, title) VALUES (?, ?)",
        (project_id, resume_item["title"]),
    )
    resume_item_id = cur.lastrowid

    cur.execute("DELETE FROM resume_highlights WHERE resume_item_id = ?", (resume_item_id,))
    for idx, h in enumerate(resume_item["highlights"]):
        cur.execute("""
            INSERT INTO resume_highlights (resume_item_id, highlight, highlight_index)
            VALUES (?, ?, ?)
        """, (resume_item_id, h, idx))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Build final JSON report from DB
# -------------------------------------------------
def assemble_report_from_db(project_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name, root, timestamp FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"No project found with id={project_id}")
    name, root, timestamp = row

    cur.execute("""
        SELECT path, file_size, created_timestamp, last_modified
        FROM files WHERE project_id = ?
    """, (project_id,))
    files = [
        {
            "file_path": r[0],
            "file_size": r[1],
            "created_timestamp": r[2],
            "last_modified": r[3],
        }
        for r in cur.fetchall()
    ]

    cur.execute("""
        SELECT file_path, function_name, start_line, end_line, cyclomatic_complexity
        FROM complexity WHERE project_id = ?
    """, (project_id,))
    complexity_functions = [
        {
            "file_path": r[0],
            "name": r[1],
            "start_line": r[2],
            "end_line": r[3],
            "cyclomatic_complexity": r[4],
        }
        for r in cur.fetchall()
    ]

    cur.execute("""
        SELECT id, name, email, commits, percent,
               total_lines_added, total_lines_deleted
        FROM contributors WHERE project_id = ?
    """, (project_id,))
    contributors = []
    for cid, cname, email, commits, percent, added, deleted in cur.fetchall():
        cur.execute("""
            SELECT filename, modifications
            FROM contributor_files
            WHERE contributor_id = ?
        """, (cid,))
        files_modified = {r[0]: r[1] for r in cur.fetchall()}
        contributors.append(
            {
                "name": cname,
                "primary_email": email,
                "commits": commits,
                "percent": percent,
                "total_lines_added": added,
                "total_lines_deleted": deleted,
                "files_modified": files_modified,
            }
        )

    cur.execute("SELECT skill, category FROM project_skills WHERE project_id = ?", (project_id,))
    resume_skills = {}
    for skill, category in cur.fetchall():
        resume_skills.setdefault(category, []).append(skill)

    cur.execute("SELECT id, title FROM resume_items WHERE project_id = ?", (project_id,))
    row = cur.fetchone()
    resume_item = None
    if row:
        resume_item_id, title = row
        cur.execute("""
            SELECT highlight FROM resume_highlights
            WHERE resume_item_id = ?
            ORDER BY highlight_index ASC
        """, (resume_item_id,))
        highlights = [r[0] for r in cur.fetchall()]
        resume_item = {"title": title, "highlights": highlights}

    conn.close()

    return {
        "project_name": name,
        "project_root": root,
        "timestamp": timestamp,
        "analyzed_files": files,
        "code_complexity": {"project_root": root, "functions": complexity_functions},
        "contributors": contributors,
        "resume_skills": resume_skills,
        "resume_item": resume_item,
    }
