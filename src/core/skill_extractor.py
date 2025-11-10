import os
import re
import requests
from dotenv import load_dotenv
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# --- NLTK setup ---
lemmatizer = WordNetLemmatizer()

# --- Load environment variables ---
load_dotenv()
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"token {token}"}

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

if __name__ == "__main__":
    analyze_repo("COSC-499-W2025", "capstone-project-team-4", branch="development")
