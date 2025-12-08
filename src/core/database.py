import sqlite3
from pathlib import Path
import json

# Path to DB = /outputs/workmine.db (shared across whole project)
DB_PATH = (
    Path(__file__).resolve().parents[2]   # from src/core → src → project root
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

    # Resume-ready skills by project
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

    # Resume item (title + unlimited bullet points stored as JSON)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            highlights TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

        # Skill extraction — project-level summary
    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_skill_summary (
            project_id INTEGER PRIMARY KEY,
            total_files INTEGER,
            files_analyzed INTEGER,
            files_skipped INTEGER,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Skill extraction — global aggregated counts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_global_skill_counts (
            project_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (project_id, skill),
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Skill extraction — heatmap/timeline
    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_skill_timeline (
            project_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (project_id, skill, date),
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)


    conn.commit()
    conn.close()
    
    print("✅ Database initialized.")


# -------------------------------------------------
# Save legacy skills
# -------------------------------------------------
def save_skills_to_db(project_path: str, skills: list[str]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM skills WHERE project_path = ?", (project_path,))
    for skill in skills:
        cur.execute(
            "INSERT INTO skills (project_path, skill) VALUES (?, ?)",
            (project_path, skill),
        )
    conn.commit()
    conn.close()


# -------------------------------------------------
# Save project + metadata + complexity + contributors
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
        contributor_id = cur.lastrowid

        for filename, count in c.get("files_modified", {}).items():
            cur.execute("""
                INSERT INTO contributor_files (contributor_id, filename, modifications)
                VALUES (?, ?, ?)
            """, (contributor_id, filename, count))

    conn.commit()
    conn.close()


# -------------------------------------------------
# Save resume-ready skills
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
# Save resume item (title + list of bullet highlights)
# -------------------------------------------------
def save_resume_item(project_id: int, resume_item: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM resume_items WHERE project_id = ?", (project_id,))
    cur.execute("""
        INSERT INTO resume_items (project_id, title, highlights)
        VALUES (?, ?, ?)
    """, (project_id, resume_item["title"], json.dumps(resume_item["highlights"])))
    conn.commit()
    conn.close()


# -------------------------------------------------
# Load résumé item from DB
# -------------------------------------------------
def get_resume_item_from_db(project_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, highlights
        FROM resume_items
        WHERE project_id = ?
    """, (project_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    title, highlights_json = row
    return {"title": title, "highlights": json.loads(highlights_json)}

#stores the extracted summary + heatmap data into the DB
def save_skill_insights(project_id: int, summary: dict, heatmap: dict):
    conn = get_connection()
    cur = conn.cursor()

    # 1) summary
    cur.execute("DELETE FROM project_skill_summary WHERE project_id = ?", (project_id,))
    cur.execute("""
        INSERT INTO project_skill_summary (
            project_id, total_files, files_analyzed, files_skipped
        ) VALUES (?, ?, ?, ?)
    """, (
        project_id,
        summary.get("total_files", 0),
        summary.get("files_analyzed", 0),
        summary.get("files_skipped", 0),
    ))

    # 2) global skill counts
    cur.execute("DELETE FROM project_global_skill_counts WHERE project_id = ?", (project_id,))
    for skill, count in summary.get("global_skill_counts", {}).items():
        cur.execute("""
            INSERT INTO project_global_skill_counts (project_id, skill, count)
            VALUES (?, ?, ?)
        """, (project_id, skill, count))

    # 3) timeline / heatmap
    cur.execute("DELETE FROM project_skill_timeline WHERE project_id = ?", (project_id,))
    for skill, date_dict in heatmap.items():
        for date, count in date_dict.items():
            cur.execute("""
                INSERT INTO project_skill_timeline (project_id, skill, date, count)
                VALUES (?, ?, ?, ?)
            """, (project_id, skill, date, count))

    conn.commit()
    conn.close()

def get_skill_timeline_for_project(project_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT skill, date, count
        FROM project_skill_timeline
        WHERE project_id = ?
    """, (project_id,))
    rows = cur.fetchall()
    conn.close()

    timeline = {}
    for skill, date, count in rows:
        timeline.setdefault(date, {})[skill] = count
    return timeline

def get_latest_project_id_for_path(project_root: str) -> int | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id
        FROM projects
        WHERE root = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (project_root,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def save_skill_timeline(project_id: int, timeline: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM project_skill_timeline WHERE project_id = ?", (project_id,))
    for skill, dates in timeline.items():
        for date, count in dates.items():
            cur.execute("""
                INSERT INTO project_skill_timeline (project_id, skill, date, count)
                VALUES (?, ?, ?, ?)
            """, (project_id, skill, date, count))
    conn.commit()
    conn.close()



# -------------------------------------------------
# Final JSON assembly from DB
# -------------------------------------------------
def assemble_report_from_db(project_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    # Project
    cur.execute("SELECT name, root, timestamp FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"No project found with id={project_id}")
    name, root, timestamp = row

    # Files
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

    # Complexity
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

    # Contributors
    cur.execute("""
        SELECT id, name, email, commits, percent,
               total_lines_added, total_lines_deleted
        FROM contributors WHERE project_id = ?
    """, (project_id,))
    contributor_rows = cur.fetchall()
    contributors = []
    for cid, cname, email, commits, percent, added, deleted in contributor_rows:
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

    # Resume skills
    cur.execute(
        "SELECT skill, category FROM project_skills WHERE project_id = ?",
        (project_id,),
    )
    rows = cur.fetchall()
    resume_skills = {}
    for skill, category in rows:
        resume_skills.setdefault(category, []).append(skill)

    # Resume item
    resume_item = get_resume_item_from_db(project_id)

    conn.close()
    return {
        "project_name": name,
        "project_root": root,
        "timestamp": timestamp,
        "analyzed_files": files,
        "code_complexity": {
            "project_root": root,
            "functions": complexity_functions,
        },
        "contributors": contributors,
        "resume_skills": resume_skills,
        "resume_item": resume_item,   # ✔ now included
    }
