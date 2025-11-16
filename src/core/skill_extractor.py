import os
import re
import base64
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from collections import defaultdict, Counter


# Download required NLTK data 
import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)


# --- NLTK setup ---
lemmatizer = WordNetLemmatizer()

# --- Load environment variables ---
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

# Allow import without token for CI & testing
if token:
    headers = {"Authorization": f"token {token}"}
else:
    headers = {}  # still allows mocked tests to run
    # Only stop if running the analyzer directly from CLI
    if __name__ == "__main__":
        raise SystemExit(
            "\n❌ Error: GitHub token not found.\n"
            "Please create a `.env` file in the project root containing:\n\n"
            "GITHUB_TOKEN=your_personal_github_token_here\n"
        )

headers = {"Authorization": f"token {token}"}

# --- Clean Printing Helpers ---

def print_section(title):
    print(f"\n=== {title} ===")

def pretty_dict(d, indent=2):
    for key, val in d.items():
        print(" " * indent + f"- {key}: {val}")

def print_table(rows, headers):
    col_widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in col_widths)

    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in col_widths]))

    for row in rows:
        print(fmt.format(*row))


# --- Predefined skill keywords ---
SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "html", "css", "sql",
    "react", "flask", "django", "node.js", "express", "pandas", "numpy", "matplotlib",
    "tensorflow", "pytorch", "docker", "kubernetes", "git", "github", "sqlite",
    "mysql", "postgresql", "fastapi"
]

# --- File extension to language map ---
EXT_TO_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".css": "CSS", ".html": "HTML", ".md": "Markdown",
    ".java": "Java", ".cs": "C#", ".cpp": "C++", ".c": "C",
    ".sql": "SQL"
}


# --- Helper: List repo contents recursively ---
def _list_contents(owner, repo, path="", ref="main"):
    base = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": ref}
    resp = requests.get(base, headers=headers, params=params)
    if resp.status_code != 200:
        return []
    items = resp.json()
    files = []
    for it in items:
        if it["type"] == "file":
            files.append(it)
        elif it["type"] == "dir":
            files.extend(_list_contents(owner, repo, it["path"], ref))
    return files


def _ext_of(name: str) -> str:
    i = name.rfind(".")
    return name[i:] if i != -1 else ""


# --- Accurate line counting per language ---
def get_language_line_counts(owner, repo, ref):
    line_counts = {}
    files = _list_contents(owner, repo, "", ref)
    for f in files:
        ext = _ext_of(f["name"]).lower()
        lang = EXT_TO_LANG.get(ext)
        if not lang:
            continue
        if f.get("size", 0) > 1024 * 1024:
            continue  # skip huge files
        fr = requests.get(f["download_url"], headers=headers)
        if fr.status_code != 200:
            continue
        text = fr.text
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        line_counts[lang] = line_counts.get(lang, 0) + lines
    return line_counts


# --- Get repo metadata and README for a specific branch ---
def get_repo_data(owner, repo, ref="main"):
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    info = requests.get(base_url, headers=headers).json()
    langs = requests.get(base_url + "/languages", headers=headers).json()

    # README for specific branch
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    readme = requests.get(readme_url, headers=headers, params={"ref": ref}).json()

    readme_text = ""
    if "content" in readme:
        import base64
        readme_text = base64.b64decode(readme["content"]).decode(errors="ignore")

    return info, langs, readme_text


# --- Extract skills from README using NLTK ---
def extract_skills(text):
    text_lower = text.lower()
    tokens = [lemmatizer.lemmatize(w) for w in word_tokenize(text_lower)]
    found = set()
    for kw in SKILL_KEYWORDS:
        if kw in tokens or kw in text_lower:
            found.add(kw)
    return sorted(found)


# --- Main function ---
def analyze_repo(owner, repo, branch=None):
    print(f"🔍 Analyzing {owner}/{repo}...")

    # Determine branch
    info, langs_bytes, _ = get_repo_data(owner, repo)
    default_branch = info.get("default_branch", "main")
    ref = branch or default_branch

    print(f"\n📦 Branch selected: {ref}")

    # Re-fetch README for correct branch
    _, langs_bytes, readme_text = get_repo_data(owner, repo, ref)

    # Line counts
    lines_exact = get_language_line_counts(owner, repo, ref)

    print("\n🧠 Languages detected:")
    if lines_exact:
        for lang, lines in sorted(lines_exact.items(), key=lambda x: (-x[1], x[0])):
            bytes_ = langs_bytes.get(lang, 0)
            if bytes_ > 0:
                print(f"  - {lang}: {lines} lines ({bytes_:,} bytes)")
            else:
                print(f"  - {lang}: {lines} lines")
    else:
        for lang, bytes_ in langs_bytes.items():
            est_lines = max(1, int(bytes_) // 16)
            print(f"  - {lang}: ~{est_lines} lines ({bytes_:,} bytes)")

    # Skill extraction
    skills = extract_skills(readme_text)
    if skills:
        print("\n🛠️  Skills found in README or code:")
        for s in skills:
            print(f"  - {s}")
    else:
        print("\n⚙️  No specific skills found in README.")

    print("\n✅ Analysis complete!")

    # ===========================
    # 🔍 GitHub Insight Sections
    # ===========================

    # --- Objective Contributions ---
    print_section("Objective Contributions")
    oc = get_objective_contributions(owner, repo)
    rows = []
    for user, stats in oc.items():
        rows.append([user, stats["commits"], stats["add"], stats["del"], stats["files"]])
    print_table(rows, ["User", "Commits", "Lines added", "Lines deleted", "Files touched"])

    # --- Development Rhythm ---
    print_section("Development Rhythm")
    dr = get_development_rhythm(owner, repo)
    for user, data in dr.items():
        print(f"- {user}")
        print(f"    Total commits: {data['total']}")
        print(f"    Weekday activity: {dict(data['weekday'])}")
        print(f"    Hour activity: {dict(data['hour'])}")

    # --- Technical Decisions ---
    print_section("Technical Decisions")
    td = get_technical_decisions(owner, repo)
    for user, counter in td.items():
        print(f"- {user}: {dict(counter)}")

    # --- Skill Growth Timeline ---
    print_section("Skill Growth Timeline")
    sg = get_skill_growth(owner, repo)
    for user, timeline in sg.items():
        print(f"- {user}:")
        for entry in timeline[-3:]:  # show last 3 entries
            print(f"    {entry['date']} → {entry['skills']}")

    # --- Role Distribution ---
    print_section("Role Distribution")
    rd = get_role_distribution(owner, repo)
    rows = []
    for user, roles in rd.items():
        rows.append([
            user,
            roles.get("commits", 0),
            roles.get("opened_prs", 0),
            roles.get("reviews", 0),
            roles.get("comments", 0)
        ])
    print_table(rows, ["User", "Commits", "PRs", "Reviews", "Comments"])

    # --- Team Culture ---
    print_section("Team Culture")
    tc = get_team_culture(owner, repo)
    pretty_dict(tc)



# --- Added Pagination Helper ---
def _get_paginated(url, params=None, max_pages=10):
    params = params.copy() if params else {}
    params.setdefault("per_page", 100)

    for page in range(1, max_pages + 1):
        params["page"] = page
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            break
        chunk = res.json()
        if not chunk:
            break
        for item in chunk:
            yield item

def get_objective_contributions(owner, repo, max_commits=300):
    stats = defaultdict(lambda: {"commits": 0, "add": 0, "del": 0, "files": set()})

    commits = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/commits"
    ))[:max_commits]

    for c in commits:
        author = c["author"]["login"] if c.get("author") else "unknown"
        sha = c["sha"]

        detail = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}",
            headers=headers).json()

        stats[author]["commits"] += 1
        stats[author]["add"] += detail["stats"].get("additions", 0)
        stats[author]["del"] += detail["stats"].get("deletions", 0)

        for f in detail.get("files", []):
            stats[author]["files"].add(f["filename"])

    # finalize file count
    for a in stats:
        stats[a]["files"] = len(stats[a]["files"])

    return stats


# --- Added the 6 GitHub API Insight Functions ---

# 1 Objective contributions

def get_objective_contributions(owner, repo, max_commits=300):
    stats = defaultdict(lambda: {"commits": 0, "add": 0, "del": 0, "files": set()})

    commits = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/commits"
    ))[:max_commits]

    for c in commits:
        author = c["author"]["login"] if c.get("author") else "unknown"
        sha = c["sha"]

        detail = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}",
            headers=headers).json()

        stats[author]["commits"] += 1
        stats[author]["add"] += detail["stats"].get("additions", 0)
        stats[author]["del"] += detail["stats"].get("deletions", 0)

        for f in detail.get("files", []):
            stats[author]["files"].add(f["filename"])

    # finalize file count
    for a in stats:
        stats[a]["files"] = len(stats[a]["files"])

    return stats

#2 Development Rhythm

def get_development_rhythm(owner, repo, max_commits=400):
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    rhythm = defaultdict(lambda: {"weekday": Counter(), "hour": Counter(), "total": 0})

    commits = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/commits"
    ))[:max_commits]

    for c in commits:
        author = c["author"]["login"] if c.get("author") else "unknown"
        dt = datetime.fromisoformat(
            c["commit"]["author"]["date"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        rhythm[author]["total"] += 1
        rhythm[author]["weekday"][weekdays[dt.weekday()]] += 1
        rhythm[author]["hour"][dt.hour] += 1

    return rhythm

#3 Technical decision-making

PREFIX_MAP = {
    "fix": "bugfix",
    "refactor": "refactor",
    "perf": "performance",
    "optimize": "performance",
    "test": "tests",
    "doc": "docs"
}

def get_technical_decisions(owner, repo, max_commits=300):
    signals = defaultdict(Counter)

    commits = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/commits"
    ))[:max_commits]

    for c in commits:
        author = c["author"]["login"] if c.get("author") else "unknown"
        msg = c["commit"]["message"].lower()
        for key, label in PREFIX_MAP.items():
            if msg.startswith(key):
                signals[author][label] += 1
    return signals

#4 Skill growth timeline

EXT_SKILL_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".java": "Java", ".cpp": "C++", ".c": "C", ".sql": "SQL"
}

def get_skill_growth(owner, repo, max_commits=400):
    commits = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/commits"
    ))[:max_commits]

    commits.sort(key=lambda c: c["commit"]["author"]["date"])

    cumulative = defaultdict(Counter)
    timeline = defaultdict(list)

    for c in commits:
        author = c["author"]["login"] if c.get("author") else "unknown"
        detail = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits/{c['sha']}",
            headers=headers).json()

        skills = set()
        for f in detail.get("files", []):
            ext = os.path.splitext(f["filename"])[1]
            if ext in EXT_SKILL_MAP:
                skills.add(EXT_SKILL_MAP[ext])
            if "test" in f["filename"].lower():
                skills.add("Testing")

        for s in skills:
            cumulative[author][s] += 1

        timeline[author].append({
            "date": c["commit"]["author"]["date"],
            "skills": dict(cumulative[author])
        })

    return timeline

#5 Role distribution

def get_role_distribution(owner, repo):
    roles = defaultdict(Counter)

    # commits
    commits = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/commits"
    ))
    for c in commits:
        author = c["author"]["login"] if c.get("author") else "unknown"
        roles[author]["commits"] += 1

    # PRs
    prs = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        params={"state": "all"}
    ))
    for pr in prs:
        opener = pr["user"]["login"]
        roles[opener]["opened_prs"] += 1

        num = pr["number"]

        reviews = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}/reviews",
            headers=headers).json()

        for r in reviews:
            reviewer = r["user"]["login"]
            roles[reviewer]["reviews"] += 1

        comments = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments",
            headers=headers).json()

        for c in comments:
            roles[c["user"]["login"]]["comments"] += 1

    return roles

#6 Team culture metrics
def get_team_culture(owner, repo):
    prs = list(_get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        params={"state": "all"}
    ))

    merged_times = []
    review_count = 0
    comment_count = 0

    for pr in prs:
        if pr.get("merged_at"):
            t1 = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            merged_times.append((t2 - t1).total_seconds() / 3600)

        num = pr["number"]

        r = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}/reviews",
            headers=headers).json()
        c = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments",
            headers=headers).json()

        review_count += len(r)
        comment_count += len(c)

    median_merge = sorted(merged_times)[len(merged_times)//2] if merged_times else 0

    return {
        "total_prs": len(prs),
        "median_merge_hours": median_merge,
        "avg_reviews": review_count / len(prs) if prs else 0,
        "avg_comments": comment_count / len(prs) if prs else 0,
    }

if __name__ == "__main__":
    analyze_repo("COSC-499-W2025", "capstone-project-team-4", branch="development")