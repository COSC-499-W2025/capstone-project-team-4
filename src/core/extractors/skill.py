"""
Skill Extraction Module (Merged)

This module extracts professional skills from detected languages, frameworks,
and file types in a project. It provides intelligent skill inference that goes
beyond simple detection to understand what capabilities are demonstrated.

This is a merged module combining:
- resume_skill_extractor.py (dictionary-based mapping)
- alternate_skill_extractor.py (regex-based code pattern detection)

Main functions:
    - analyze_project_skills(): Comprehensive project skill analysis
    - extract_resume_skills(): Extract all skills from a project
    - extract_skills_from_languages(): Get skills from programming languages
    - extract_skills_from_frameworks(): Get skills from frameworks/libraries
    - extract_skills_from_files(): Get skills from file types
    - analyze_code_patterns(): Regex-based skill detection from code

Migrated from:
- src/core/resume_skill_extractor.py
- src/core/alternate_skill_extractor.py
"""

import json
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any

from src.core.constants import SKIP_DIRECTORIES

logger = logging.getLogger(__name__)


# =============================================================================
# Language to skills mapping
# =============================================================================

LANGUAGE_SKILLS: Dict[str, List[str]] = {
    # General Purpose Languages
    "Python": [],
    "Java": ["Object-Oriented Programming"],
    "C#": ["Object-Oriented Programming"],
    "Go": [],
    "Rust": [],
    "PHP": [],
    "Ruby": [],
    "Kotlin": ["Object-Oriented Programming"],
    "Scala": ["Functional Programming"],
    "Elixir": ["Functional Programming"],
    "Erlang": ["Functional Programming"],
    # Frontend Languages
    "JavaScript": [],
    "TypeScript": [],
    "HTML": [],
    "CSS": [],
    # Mobile Languages
    "Swift": ["iOS Development"],
    "Dart": [],
    # Systems & Low-Level
    "C": [],
    "C++": ["Object-Oriented Programming"],
    "Assembly": [],
    # Data & Scientific
    "R": ["Statistical Analysis"],
    "Julia": ["Scientific Computing"],
    "MATLAB": ["Scientific Computing"],
    # Scripting Languages
    "Shell": ["Automation"],
    "PowerShell": ["Automation"],
    "Batch": ["Automation"],
    "Perl": [],
    "Lua": [],
    "Groovy": [],
    # Functional Languages
    "Haskell": ["Functional Programming"],
    "F#": ["Functional Programming"],
    # Query Language
    "SQL": ["Database Querying"],
    # Markup/Data Formats
    "JSON": [],
    "XML": [],
    "YAML": [],
    # Notebooks
    "Jupyter Notebook": ["Data Analysis"],
}


# =============================================================================
# Framework to skills mapping
# =============================================================================

FRAMEWORK_SKILLS: Dict[str, List[str]] = {
    # Python Web Frameworks
    "Django": ["RESTful APIs", "ORM", "MVC Architecture"],
    "Flask": ["RESTful APIs"],
    "FastAPI": ["RESTful APIs", "Async Programming", "API Documentation"],
    # Python Data Science & ML
    "TensorFlow": ["Machine Learning", "Deep Learning", "Neural Networks"],
    "PyTorch": ["Machine Learning", "Deep Learning", "Neural Networks"],
    "Keras": ["Machine Learning", "Deep Learning", "Neural Networks"],
    "Scikit-learn": ["Machine Learning", "Statistical Modeling"],
    "Pandas": ["Data Analysis", "Data Manipulation"],
    "NumPy": ["Numerical Computing", "Scientific Computing"],
    "Streamlit": ["Data Visualization", "Interactive Dashboards"],
    "Gradio": ["Machine Learning Interfaces", "Interactive Demos"],
    # Python Tools
    "Celery": ["Task Queue Management", "Asynchronous Processing"],
    "Scrapy": ["Web Scraping", "Data Extraction"],
    "SQLAlchemy": ["ORM"],
    "Pytest": ["Unit Testing", "Test-Driven Development"],
    "Poetry": ["Dependency Management"],
    # JavaScript Frontend Frameworks
    "React": ["Component-Based Architecture"],
    "Vue": ["Reactive UI"],
    "Angular": ["Dependency Injection", "RxJS"],
    "Svelte": ["Compiled Components", "Reactive UI"],
    "Solid.js": ["Fine-Grained Reactivity"],
    "Preact": [],
    # Meta-Frameworks
    "Next.js": ["Server-Side Rendering", "Static Site Generation"],
    "Nuxt.js": ["Server-Side Rendering"],
    "Gatsby": ["Static Site Generation", "JAMstack", "GraphQL"],
    "Remix": ["Nested Routing", "Progressive Enhancement"],
    "Astro": ["Static Site Generation", "Partial Hydration"],
    "SvelteKit": ["Server-Side Rendering"],
    # Backend JavaScript/Node.js
    "Express": ["RESTful APIs", "Middleware"],
    "Koa": ["RESTful APIs", "Async/Await"],
    "Fastify": ["High-Performance APIs", "Schema Validation"],
    "Hapi": ["Enterprise APIs", "Plugin Architecture"],
    "NestJS": ["Enterprise Architecture", "Dependency Injection"],
    "Apollo Server": ["GraphQL Server", "Schema Design"],
    # State Management
    "Redux": ["State Management", "Predictable State Container"],
    "MobX": ["State Management", "Observable State"],
    "Zustand": ["State Management"],
    "Recoil": ["State Management", "Atomic State"],
    "Vuex": ["State Management"],
    "Pinia": ["State Management"],
    # UI Component Libraries
    "Material-UI": [],
    "Ant Design": ["Enterprise UI"],
    "Chakra UI": ["Accessible Design", "Design System"],
    "Semantic UI": ["Theming"],
    "Headless UI": ["Accessible Components"],
    "React Bootstrap": [],
    "Vuetify": [],
    "Mantine": [],
    # CSS Frameworks
    "Tailwind CSS": ["Utility-First CSS", "Responsive Design"],
    "Bootstrap": ["Responsive Design", "Grid System"],
    "Bulma": ["Responsive Design"],
    "Sass": ["CSS Preprocessing"],
    "Less": ["CSS Preprocessing"],
    "Emotion": ["CSS-in-JS"],
    "Styled Components": ["CSS-in-JS"],
    # Testing Frameworks
    "Jest": ["Unit Testing", "Test-Driven Development"],
    "Vitest": ["Unit Testing"],
    "Mocha": ["Unit Testing", "Test-Driven Development"],
    "Jasmine": ["Unit Testing", "Behavior-Driven Development"],
    "Cypress": ["End-to-End Testing", "Test Automation"],
    "Playwright": ["End-to-End Testing", "Cross-Browser Testing"],
    "Testing Library": ["Component Testing", "User-Centric Testing"],
    # Build Tools
    "Webpack": ["Build Optimization"],
    "Vite": [],
    "Rollup": [],
    "Parcel": [],
    "esbuild": [],
    "Turbopack": [],
    # GraphQL
    "GraphQL": ["GraphQL", "API Design", "Data Fetching"],
    "Apollo Client": ["GraphQL", "State Management", "Data Fetching"],
    "Relay": ["GraphQL", "Data Management"],
    "URQL": ["GraphQL", "Data Fetching"],
    # ORM & Database
    "Prisma": ["ORM"],
    "TypeORM": ["ORM"],
    "Sequelize": ["ORM"],
    "Mongoose": ["ODM", "NoSQL"],
    "Drizzle ORM": ["ORM"],
    # Mobile Frameworks
    "React Native": ["Mobile Development", "Cross-Platform Development"],
    "Expo": ["Mobile Development"],
    "Ionic": ["Hybrid Mobile Apps", "Cross-Platform Development"],
    "NativeScript": ["Cross-Platform Development"],
    "Flutter": ["Mobile Development", "Cross-Platform Development"],
    # Desktop Frameworks
    "Electron": ["Desktop Application Development", "Cross-Platform Desktop"],
    "Tauri": ["Desktop Application Development"],
    # Java Frameworks
    "Spring Boot": ["Enterprise Java", "Microservices", "RESTful APIs"],
    "Spring": ["Enterprise Java", "Dependency Injection"],
    "Hibernate": ["ORM", "Java Persistence"],
    "JUnit": ["Unit Testing", "Test-Driven Development"],
    "Mockito": ["Mocking", "Unit Testing"],
    "Ktor": ["Asynchronous APIs"],
    # Ruby Frameworks
    "Rails": ["MVC Architecture", "RESTful APIs", "Convention over Configuration"],
    "Sinatra": ["Lightweight Web Apps"],
    "Hanami": [],
    "RSpec": ["Behavior-Driven Development"],
    "Capybara": ["Integration Testing", "Web Testing"],
    # PHP Frameworks
    "Laravel": ["MVC Architecture", "Eloquent ORM"],
    "Symfony": ["Component-Based Architecture", "Enterprise Development"],
    "CodeIgniter": [],
    "CakePHP": ["Rapid Development"],
    "Yii": ["High-Performance Applications"],
    "Slim": [],
    "PHPUnit": ["Unit Testing", "Test-Driven Development"],
    # Go Frameworks
    "Gin": ["RESTful APIs", "High-Performance Web"],
    "Echo": ["RESTful APIs"],
    "Fiber": ["High-Performance APIs"],
    "Beego": ["MVC Architecture"],
    "Chi": ["RESTful APIs", "HTTP Routing"],
    "Gorilla": ["HTTP Routing"],
    "GORM": ["ORM"],
    # Rust Frameworks
    "Actix": ["High-Performance Web", "Actor Model"],
    "Rocket": ["Type-Safe APIs"],
    "Axum": ["Async APIs"],
    "Warp": [],
    "Tokio": ["Async Programming", "Concurrency"],
    "Serde": ["Serialization"],
    # .NET Frameworks
    "ASP.NET Core": ["Cross-Platform Web", "Enterprise Development"],
    "Entity Framework": ["ORM"],
    "Blazor": ["WebAssembly", "Interactive Web"],
    "xUnit": ["Unit Testing", "Test-Driven Development"],
    "NUnit": ["Unit Testing", "Test-Driven Development"],
    # Other Libraries
    "Three.js": ["3D Graphics", "WebGL", "Interactive Visualization"],
    "D3.js": ["Data Visualization", "Interactive Charts"],
    "Socket.IO": ["Real-Time Communication", "WebSockets"],
    "Axios": [],
    "Docker": ["Containerization"],
}


# =============================================================================
# File extension to skills mapping
# =============================================================================

FILE_TYPE_SKILLS: Dict[str, List[str]] = {
    # Design Files - Adobe Creative Suite
    ".psd": ["Adobe Photoshop", "Photo Editing", "Graphic Design", "Digital Art"],
    ".ai": ["Adobe Illustrator", "Vector Graphics", "Graphic Design", "Logo Design"],
    ".eps": ["Vector Graphics", "Print Design", "Adobe Illustrator"],
    # Design Files - Modern Tools
    ".sketch": ["Sketch", "UI/UX Design", "Interface Design", "Prototyping"],
    ".fig": ["Figma", "UI/UX Design", "Collaborative Design", "Prototyping"],
    # Photography - RAW Formats
    ".raw": ["Photography", "RAW Photo Processing", "Professional Photography"],
    ".cr2": ["Photography", "Canon RAW Processing", "Professional Photography"],
    ".nef": ["Photography", "Nikon RAW Processing", "Professional Photography"],
    ".arw": ["Photography", "Sony RAW Processing", "Professional Photography"],
    # Standard Image Formats
    ".jpg": ["Photography", "Image Editing"],
    ".jpeg": ["Photography", "Image Editing"],
    ".png": ["Image Editing", "Digital Graphics"],
    ".webp": ["Modern Web Graphics", "Image Optimization"],
    # Vector & Scalable Graphics
    ".svg": ["Vector Graphics", "Scalable Design", "Web Graphics"],
    # Video Files
    ".mp4": ["Video Editing", "Multimedia Production"],
    ".avi": ["Video Editing", "Multimedia Production"],
    ".mov": ["Video Editing", "Multimedia Production"],
    ".wmv": ["Video Editing", "Multimedia Production"],
    ".flv": ["Video Editing", "Streaming Media"],
    ".webm": ["Web Video", "Modern Video Formats"],
    # Audio Files
    ".mp3": ["Audio Editing", "Music Production"],
    ".wav": ["Audio Editing", "Professional Audio", "Music Production"],
    ".flac": ["Audio Engineering", "Lossless Audio", "Music Production"],
    ".aac": ["Audio Editing", "Audio Compression"],
    ".ogg": ["Audio Editing", "Open-Source Audio"],
    # 3D & CAD
    ".blend": ["Blender", "3D Modeling", "3D Animation"],
    ".obj": ["3D Modeling", "3D Graphics"],
    ".fbx": ["3D Modeling", "3D Animation", "Game Development"],
    ".stl": ["3D Modeling", "3D Printing", "CAD"],
    ".dwg": ["AutoCAD", "CAD", "Technical Drawing"],
    # Documents & Technical Writing
    ".tex": ["LaTeX", "Technical Writing", "Document Preparation"],
    ".bib": ["Bibliography Management", "Academic Writing", "LaTeX"],
    ".md": ["Markdown", "Documentation", "Technical Writing"],
    ".rst": ["reStructuredText", "Documentation", "Python Documentation"],
    # Configuration & DevOps
    ".dockerfile": ["Containerization"],
    ".dockerignore": ["Containerization"],
    "docker-compose.yml": ["Containerization", "Multi-Container Applications"],
    ".gitlab-ci.yml": ["Continuous Integration", "DevOps"],
    ".travis.yml": ["Continuous Integration", "DevOps"],
    "jenkinsfile": ["CI/CD", "Build Automation", "DevOps"],
    ".circleci/config.yml": ["Continuous Integration", "DevOps"],
    # Database
    ".sql": ["SQL", "Database Design", "Query Optimization"],
    ".db": ["Database Management", "SQLite"],
    ".sqlite": ["SQLite", "Database Management"],
    # Jupyter & Data Science
    ".ipynb": ["Jupyter Notebooks", "Data Analysis", "Interactive Computing", "Data Science"],
}


# =============================================================================
# Regex-based code pattern detection (from alternate_skill_extractor)
# =============================================================================

SUPPORTED_LANGUAGES_FOR_PATTERNS = {
    "javascript", "typescript", "java", "python", "c", "c++", "c#",
    "go", "rust", "php", "ruby", "shell", "powershell", "html",
    "css", "yaml", "json", "markdown", "sql"
}


def get_skill_mapping_path(language: str) -> Optional[str]:
    """
    Get the path to the skill mapping JSON file for a language.

    Args:
        language: Programming language name

    Returns:
        Path to the mapping file if it exists, None otherwise
    """
    base_dir = Path(__file__).parent.parent.parent / "data"
    mapping = base_dir / f"skill_mapping_{language.lower()}.json"
    return str(mapping) if mapping.exists() else None


def _load_skill_mapping(path: str) -> Dict[str, List[str]]:
    """Load skill mapping from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return {entry["skill"]: entry["identifiers"] for entry in json.load(f)}


def _safe_read_file(path: str) -> str:
    """Read file safely with fallback encodings."""
    for enc in ["utf-8", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            pass
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def analyze_code_patterns(
    file_path: str,
    language: str,
    created_ts: Optional[float] = None,
    modified_ts: Optional[float] = None,
) -> Optional[tuple[Dict[str, int], Optional[float]]]:
    """
    Analyze a code file for skill patterns using regex.

    Args:
        file_path: Path to the code file
        language: Programming language of the file
        created_ts: File creation timestamp
        modified_ts: File modification timestamp

    Returns:
        Tuple of (skill_match_counts, timestamp) or None if analysis failed
    """
    mapping_path = get_skill_mapping_path(language)
    if mapping_path is None:
        return None

    mapping = _load_skill_mapping(mapping_path)
    if not os.path.exists(file_path):
        return None

    text = _safe_read_file(file_path)
    ts = modified_ts or created_ts

    skill_match_counts: Dict[str, int] = {}

    for skill, patterns in mapping.items():
        total = 0
        for pat in patterns:
            try:
                total += len(re.findall(pat, text))
            except re.error:
                continue

        if total > 0:
            skill_match_counts[skill] = total

    return skill_match_counts, ts


def run_code_pattern_extraction(
    metadata_path: str,
) -> Dict[str, Any]:
    """
    Run regex-based skill extraction on files from metadata.

    Args:
        metadata_path: Path to the project metadata JSON file

    Returns:
        Dictionary with summary and file reports
    """
    if not os.path.exists(metadata_path):
        return {"error": f"Metadata not found: {metadata_path}"}

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    project_root = meta["project_root"]
    files = meta["files"]

    summary: Dict[str, Any] = {
        "total_files": len(files),
        "files_analyzed": 0,
        "files_skipped": 0,
        "languages_encountered": set(),
        "unsupported_languages": {},
        "global_skill_counts": defaultdict(int),
    }

    heatmap: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    file_reports: List[Dict[str, Any]] = []

    for f in files:
        lang = f.get("language", "").lower()
        rel = f.get("path")
        created_ts = f.get("created_timestamp")
        modified_ts = f.get("last_modified")

        if lang not in SUPPORTED_LANGUAGES_FOR_PATTERNS:
            summary["unsupported_languages"][lang] = summary["unsupported_languages"].get(lang, 0) + 1
            summary["files_skipped"] += 1
            continue

        summary["languages_encountered"].add(lang)
        absolute_path = os.path.join(project_root, rel)

        result = analyze_code_patterns(absolute_path, lang, created_ts, modified_ts)
        if result is None:
            summary["files_skipped"] += 1
            continue

        skill_counts, ts = result

        file_reports.append({
            "file_path": absolute_path,
            "language": lang,
            "skills": skill_counts,
            "timestamp": ts,
        })

        for skill, count in skill_counts.items():
            summary["global_skill_counts"][skill] += count
            if ts:
                date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                heatmap[skill][date] += count

        summary["files_analyzed"] += 1

    summary["languages_encountered"] = sorted(list(summary["languages_encountered"]))
    summary["global_skill_counts"] = dict(
        sorted(summary["global_skill_counts"].items(), key=lambda x: x[1], reverse=True)
    )
    heatmap_dict = {skill: dict(days) for skill, days in heatmap.items()}

    return {
        "summary": summary,
        "file_reports": file_reports,
        "heatmap": heatmap_dict,
    }


# =============================================================================
# Main skill extraction functions
# =============================================================================

def extract_skills_from_languages(languages: List[str]) -> Set[str]:
    """
    Extract skills from detected programming languages.

    Args:
        languages: List of detected programming languages

    Returns:
        Set of skills derived from the languages
    """
    skills = set()

    for language in languages:
        if language in LANGUAGE_SKILLS:
            skills.update(LANGUAGE_SKILLS[language])

    # Web Design skill when HTML + CSS are detected together
    if "HTML" in languages and "CSS" in languages:
        skills.add("Web Design")

    return skills


def extract_skills_from_frameworks(frameworks: List[str]) -> Set[str]:
    """
    Extract skills from detected frameworks and libraries.

    Args:
        frameworks: List of detected frameworks

    Returns:
        Set of skills derived from the frameworks
    """
    skills = set()

    for framework in frameworks:
        if framework in FRAMEWORK_SKILLS:
            skills.update(FRAMEWORK_SKILLS[framework])

    framework_set = set(frameworks)

    # ML Engineering - multiple ML frameworks
    ml_frameworks = {"TensorFlow", "PyTorch", "Keras", "Scikit-learn"}
    if len(framework_set & ml_frameworks) >= 2:
        skills.add("Machine Learning Engineering")

    # Testing Expertise - multiple testing frameworks
    test_frameworks = {"Jest", "Pytest", "Cypress", "Playwright", "JUnit", "Vitest", "Mocha", "RSpec"}
    if len(framework_set & test_frameworks) >= 2:
        skills.add("Test Automation")

    return skills


def extract_skills_from_files(root_dir: Union[str, Path]) -> Set[str]:
    """
    Extract skills from file types in a project.

    Args:
        root_dir: Path to the project directory

    Returns:
        Set of skills derived from file types
    """
    root_path = Path(root_dir)
    skills = set()
    file_counter: Counter = Counter()

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRECTORIES]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()

            if filename.lower() in FILE_TYPE_SKILLS:
                skills.update(FILE_TYPE_SKILLS[filename.lower()])

            if ext in FILE_TYPE_SKILLS:
                file_counter[ext] += 1

    # Apply thresholds for skill detection
    photo_raw_exts = {".raw", ".cr2", ".nef", ".arw"}
    photo_count = sum(file_counter[ext] for ext in photo_raw_exts if ext in file_counter)
    if photo_count >= 3:
        skills.add("Photography")
        skills.add("RAW Photo Processing")

    standard_photo_exts = {".jpg", ".jpeg"}
    standard_photo_count = sum(file_counter[ext] for ext in standard_photo_exts if ext in file_counter)
    if standard_photo_count >= 10:
        skills.add("Photography")

    for ext in [".psd", ".ai", ".sketch", ".fig"]:
        if file_counter.get(ext, 0) >= 1:
            skills.update(FILE_TYPE_SKILLS[ext])

    video_exts = {".mp4", ".avi", ".mov", ".wmv"}
    video_count = sum(file_counter[ext] for ext in video_exts if ext in file_counter)
    if video_count >= 2:
        skills.add("Video Editing")
        skills.add("Multimedia Production")

    audio_exts = {".wav", ".flac", ".aac"}
    audio_count = sum(file_counter[ext] for ext in audio_exts if ext in file_counter)
    if audio_count >= 3:
        skills.add("Audio Editing")
        skills.add("Music Production")

    modeling_exts = {".blend", ".obj", ".fbx", ".stl"}
    if any(file_counter.get(ext, 0) >= 1 for ext in modeling_exts):
        skills.add("3D Modeling")

    if file_counter.get(".tex", 0) >= 1:
        skills.update(FILE_TYPE_SKILLS[".tex"])

    if file_counter.get(".md", 0) >= 5:
        skills.add("Documentation")
        skills.add("Technical Writing")

    if file_counter.get(".ipynb", 0) >= 1:
        skills.update(FILE_TYPE_SKILLS[".ipynb"])

    return skills


def _infer_contextual_skills(languages: List[str], frameworks: List[str]) -> Set[str]:
    """
    Infer contextual skills based on language + framework combinations.

    Args:
        languages: List of detected languages
        frameworks: List of detected frameworks

    Returns:
        Set of inferred contextual skills
    """
    skills = set()
    lang_set = set(languages)
    framework_set = set(frameworks)

    backend_langs = {"Python", "Java", "C#", "Go", "Rust", "PHP", "Ruby", "Kotlin", "Scala", "Elixir", "Erlang"}
    backend_frameworks = {
        "Django", "Flask", "FastAPI", "Express", "Koa", "Fastify", "Hapi",
        "NestJS", "Spring Boot", "Spring", "Rails", "Sinatra", "Laravel",
        "Symfony", "Gin", "Echo", "Fiber", "Actix", "Rocket", "ASP.NET Core"
    }

    frontend_langs = {"JavaScript", "TypeScript"}
    frontend_frameworks = {
        "React", "Vue", "Angular", "Svelte", "Solid.js", "Preact",
        "Next.js", "Nuxt.js", "Gatsby", "Remix", "Astro", "SvelteKit"
    }

    has_backend = bool(lang_set & backend_langs)
    has_modern_frontend = (lang_set & frontend_langs) and (framework_set & frontend_frameworks)
    has_traditional_frontend = ("HTML" in lang_set) or ("CSS" in lang_set)
    has_frontend = has_modern_frontend or has_traditional_frontend

    if has_backend and has_frontend:
        skills.add("Full-Stack Development")
    else:
        if has_backend:
            skills.add("Backend Development")
        if has_modern_frontend:
            skills.add("Frontend Development")
        elif has_traditional_frontend and not has_backend:
            skills.add("Frontend Development")

    mobile_frameworks = {"React Native", "Expo", "Ionic", "NativeScript", "Flutter"}

    if "Swift" in lang_set:
        skills.add("Mobile Development")

    if "Dart" in lang_set and "Flutter" in framework_set:
        skills.add("Mobile Development")

    if (lang_set & frontend_langs) and (framework_set & mobile_frameworks):
        skills.add("Mobile Development")

    if "Python" in lang_set:
        data_frameworks = {"Pandas", "NumPy", "Scikit-learn", "Jupyter Notebook"}
        if framework_set & data_frameworks:
            skills.add("Data Science")

    if "R" in lang_set:
        skills.add("Data Science")

    ml_frameworks = {"TensorFlow", "PyTorch", "Keras", "Scikit-learn"}
    if framework_set & ml_frameworks:
        skills.add("Machine Learning")

    has_containers = "Docker" in framework_set
    has_scripting = lang_set & {"Shell", "PowerShell", "Batch"}

    if has_containers and has_scripting:
        skills.add("DevOps")

    return skills


def extract_resume_skills(
    root_dir: Union[str, Path],
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    include_code_patterns: bool = False,
) -> List[str]:
    """
    Extract comprehensive resume-ready skills from a project.

    Args:
        root_dir: Path to the project directory
        languages: Optional pre-detected list of languages
        frameworks: Optional pre-detected list of frameworks
        include_code_patterns: If True, also run regex-based code pattern analysis

    Returns:
        Sorted list of unique skills
    """
    root_path = Path(root_dir)
    all_skills: Set[str] = set()

    # Get languages if not provided
    if languages is None:
        from src.core.analyzers.language import ProjectAnalyzer
        analyzer = ProjectAnalyzer()
        language_stats = analyzer.analyze_project_languages(str(root_path))
        languages = [lang for lang, count in language_stats.items() if lang != "Unknown" and count > 0]

    # Get frameworks if not provided
    if frameworks is None:
        from src.core.extractors.framework import detect_frameworks_recursive
        rules_path = Path(__file__).parent.parent / "rules" / "frameworks.yml"
        if rules_path.exists():
            fw_results = detect_frameworks_recursive(root_path, str(rules_path))
            frameworks = []
            for folder_frameworks in fw_results.get("frameworks", {}).values():
                for fw in folder_frameworks:
                    frameworks.append(fw.get("name", ""))
        else:
            logger.warning("Framework rules file not found at %s", rules_path)
            frameworks = []

    all_skills.update(extract_skills_from_languages(languages))
    all_skills.update(extract_skills_from_frameworks(frameworks))
    all_skills.update(extract_skills_from_files(root_path))
    all_skills.update(_infer_contextual_skills(languages, frameworks))

    return sorted(list(all_skills))


def get_skill_categories() -> Dict[str, List[str]]:
    """
    Return a categorized view of all possible skills.

    Returns:
        Dictionary mapping skill categories to lists of skills
    """
    categories: Dict[str, Set[str]] = {
        "Programming Languages": set(),
        "Web Development": set(),
        "Mobile Development": set(),
        "Data Science & ML": set(),
        "Design & Creative": set(),
        "DevOps & Infrastructure": set(),
        "Testing & QA": set(),
        "Database & ORM": set(),
        "Other": set(),
    }

    for skills in LANGUAGE_SKILLS.values():
        for skill in skills:
            if any(keyword in skill for keyword in ["Programming", "Development", "Scripting"]):
                categories["Programming Languages"].add(skill)

    for skills in FRAMEWORK_SKILLS.values():
        for skill in skills:
            if any(keyword in skill for keyword in ["Machine Learning", "Data Science", "AI", "Deep Learning"]):
                categories["Data Science & ML"].add(skill)
            elif any(keyword in skill for keyword in ["Mobile", "iOS", "Android"]):
                categories["Mobile Development"].add(skill)
            elif any(keyword in skill for keyword in ["Testing", "Test-Driven", "QA", "Quality"]):
                categories["Testing & QA"].add(skill)
            elif any(keyword in skill for keyword in ["DevOps", "Docker", "CI/CD", "Container"]):
                categories["DevOps & Infrastructure"].add(skill)
            elif any(keyword in skill for keyword in ["ORM", "Database", "SQL"]):
                categories["Database & ORM"].add(skill)
            elif any(keyword in skill for keyword in ["Frontend", "Backend", "Web", "API"]):
                categories["Web Development"].add(skill)

    for skills in FILE_TYPE_SKILLS.values():
        for skill in skills:
            if any(keyword in skill for keyword in ["Design", "Photo", "Video", "Audio", "3D", "Graphics"]):
                categories["Design & Creative"].add(skill)

    return {k: sorted(list(v)) for k, v in categories.items() if v}


def analyze_project_skills(
    root_dir: Union[str, Path],
    include_code_patterns: bool = False,
) -> Dict[str, Any]:
    """
    Comprehensive project skill analysis.

    Args:
        root_dir: Path to the project directory
        include_code_patterns: If True, also run regex-based code pattern analysis

    Returns:
        Dictionary containing languages, frameworks, skills, and skill categories
    """
    root_path = Path(root_dir)

    # Extract languages
    from src.core.analyzers.language import ProjectAnalyzer
    analyzer = ProjectAnalyzer()
    language_stats = analyzer.analyze_project_languages(str(root_path))
    languages = [lang for lang, count in language_stats.items() if lang != "Unknown" and count > 0]

    # Extract frameworks
    from src.core.extractors.framework import detect_frameworks_recursive
    rules_path = Path(__file__).parent.parent / "rules" / "frameworks.yml"
    if rules_path.exists():
        fw_results = detect_frameworks_recursive(root_path, str(rules_path))
        best: Dict[str, float] = {}
        for folder_frameworks in fw_results.get("frameworks", {}).values():
            for fw in folder_frameworks:
                name = (fw.get("name") or "").strip()
                if not name:
                    continue
                conf = fw.get("confidence", 1.0)
                if name not in best or conf > best[name]:
                    best[name] = conf
        frameworks = [name for name, _ in sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))]
    else:
        logger.warning("Framework rules file not found at %s", rules_path)
        frameworks = []

    # Extract all skills
    skills = extract_resume_skills(root_path, languages, frameworks, include_code_patterns)

    # Categorize skills
    categories = get_skill_categories()
    categorized_skills: Dict[str, List[str]] = {}

    for skill in skills:
        placed = False
        for category, category_skills in categories.items():
            if skill in category_skills:
                if category not in categorized_skills:
                    categorized_skills[category] = []
                categorized_skills[category].append(skill)
                placed = True
                break

        if not placed:
            if "Other" not in categorized_skills:
                categorized_skills["Other"] = []
            categorized_skills["Other"].append(skill)

    return {
        "languages": languages,
        "frameworks": frameworks,
        "skills": skills,
        "skill_categories": categorized_skills,
        "total_skills": len(skills),
        "project_path": str(root_path.resolve()),
    }
