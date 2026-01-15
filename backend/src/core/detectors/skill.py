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

# =============================================================================
# Library to skills mapping
# =============================================================================

LIBRARY_SKILLS: Dict[str, List[str]] = {
    # HTTP Clients
    "axios": ["HTTP Client", "RESTful APIs", "Async Programming"],
    "fetch": ["HTTP Client", "RESTful APIs"],
    "httpx": ["HTTP Client", "RESTful APIs", "Async Programming"],
    "requests": ["HTTP Client", "RESTful APIs"],
    "aiohttp": ["HTTP Client", "Async Programming"],
    "got": ["HTTP Client", "RESTful APIs"],
    "superagent": ["HTTP Client", "RESTful APIs"],

    # Utility Libraries
    "lodash": ["Utility Libraries", "Functional Programming"],
    "underscore": ["Utility Libraries", "Functional Programming"],
    "ramda": ["Functional Programming"],
    "date-fns": ["Date/Time Manipulation"],
    "moment": ["Date/Time Manipulation"],
    "dayjs": ["Date/Time Manipulation"],
    "uuid": ["Unique ID Generation"],

    # Data Processing
    "pandas": ["Data Analysis", "Data Manipulation", "Data Processing"],
    "numpy": ["Numerical Computing", "Scientific Computing", "Data Processing"],
    "scipy": ["Scientific Computing", "Statistical Analysis"],
    "polars": ["Data Analysis", "Data Processing"],
    "dask": ["Distributed Computing", "Big Data Processing"],
    "vaex": ["Big Data Processing", "Data Analysis"],

    # Validation
    "zod": ["Schema Validation", "Type Safety"],
    "yup": ["Schema Validation", "Form Validation"],
    "joi": ["Schema Validation", "API Validation"],
    "pydantic": ["Data Validation", "Type Safety"],
    "cerberus": ["Data Validation"],
    "marshmallow": ["Data Serialization", "Schema Validation"],

    # Authentication
    "passport": ["Authentication", "OAuth"],
    "jsonwebtoken": ["JWT Authentication", "Security"],
    "bcrypt": ["Password Hashing", "Security"],
    "argon2": ["Password Hashing", "Security"],
    "pyjwt": ["JWT Authentication", "Security"],

    # Logging
    "winston": ["Logging", "Application Monitoring"],
    "pino": ["Logging", "Application Monitoring"],
    "bunyan": ["Logging"],
    "loguru": ["Logging", "Application Monitoring"],

    # Database Clients
    "pg": ["PostgreSQL", "Database Management"],
    "mysql2": ["MySQL", "Database Management"],
    "redis": ["Redis", "Caching", "In-Memory Database"],
    "mongodb": ["MongoDB", "NoSQL"],
    "psycopg2": ["PostgreSQL", "Database Management"],
    "pymongo": ["MongoDB", "NoSQL"],
    "asyncpg": ["PostgreSQL", "Async Programming", "Database Management"],

    # Message Queues
    "amqplib": ["Message Queues", "RabbitMQ"],
    "bull": ["Job Queues", "Background Processing"],
    "celery": ["Task Queue Management", "Background Processing"],
    "rq": ["Job Queues", "Background Processing"],
    "kafka-python": ["Apache Kafka", "Event Streaming"],

    # Image Processing
    "sharp": ["Image Processing", "Image Optimization"],
    "jimp": ["Image Processing"],
    "pillow": ["Image Processing", "Computer Vision"],
    "opencv-python": ["Computer Vision", "Image Processing"],

    # File Processing
    "multer": ["File Upload Handling"],
    "formidable": ["File Upload Handling"],
    "python-magic": ["File Type Detection"],

    # PDF Processing
    "pdfkit": ["PDF Generation"],
    "puppeteer": ["Browser Automation", "PDF Generation", "Web Scraping"],
    "reportlab": ["PDF Generation"],
    "pypdf2": ["PDF Processing"],

    # Email
    "nodemailer": ["Email Integration", "SMTP"],
    "sendgrid": ["Email Integration", "Email API"],

    # WebSockets
    "socket.io": ["Real-Time Communication", "WebSockets"],
    "ws": ["WebSockets", "Real-Time Communication"],
    "websockets": ["WebSockets", "Real-Time Communication"],

    # CLI
    "commander": ["CLI Development"],
    "yargs": ["CLI Development"],
    "inquirer": ["CLI Development", "Interactive CLI"],
    "click": ["CLI Development"],
    "typer": ["CLI Development"],

    # ML/AI Libraries
    "transformers": ["Natural Language Processing", "Machine Learning"],
    "huggingface": ["Natural Language Processing", "Machine Learning"],
    "openai": ["AI Integration", "GPT API"],
    "langchain": ["LLM Applications", "AI Integration"],
    "spacy": ["Natural Language Processing"],
    "nltk": ["Natural Language Processing"],
    "gensim": ["Natural Language Processing", "Topic Modeling"],

    # Web Scraping
    "cheerio": ["Web Scraping", "HTML Parsing"],
    "beautifulsoup4": ["Web Scraping", "HTML Parsing"],
    "scrapy": ["Web Scraping", "Data Extraction"],
    "selenium": ["Browser Automation", "Web Scraping"],

    # Visualization
    "chart.js": ["Data Visualization", "Charts"],
    "d3": ["Data Visualization", "Interactive Charts"],
    "plotly": ["Data Visualization", "Interactive Charts"],
    "matplotlib": ["Data Visualization", "Charts"],
    "seaborn": ["Data Visualization", "Statistical Graphics"],
    "bokeh": ["Data Visualization", "Interactive Charts"],
    "altair": ["Data Visualization", "Declarative Charts"],

    # Cloud SDKs
    "aws-sdk": ["AWS", "Cloud Infrastructure"],
    "boto3": ["AWS", "Cloud Infrastructure"],
    "@google-cloud": ["Google Cloud", "Cloud Infrastructure"],
    "google-cloud": ["Google Cloud", "Cloud Infrastructure"],
    "@azure": ["Azure", "Cloud Infrastructure"],
    "azure": ["Azure", "Cloud Infrastructure"],

    # Monitoring
    "prometheus-client": ["Monitoring", "Metrics"],
    "prom-client": ["Monitoring", "Metrics"],
    "sentry": ["Error Tracking", "Application Monitoring"],
    "@sentry/node": ["Error Tracking", "Application Monitoring"],
    "newrelic": ["Application Performance Monitoring"],
    "datadog": ["Application Performance Monitoring", "Monitoring"],
}


# =============================================================================
# Tool to skills mapping
# =============================================================================

TOOL_SKILLS: Dict[str, List[str]] = {
    # Build Tools
    "Webpack": ["Build Optimization", "Module Bundling"],
    "Vite": ["Modern Build Tools", "Fast Development"],
    "Rollup": ["Module Bundling", "Library Packaging"],
    "esbuild": ["Fast Build Tools", "TypeScript Compilation"],
    "Parcel": ["Zero-Config Bundling"],
    "Turbopack": ["Fast Build Tools"],

    # CI/CD
    "GitHub Actions": ["CI/CD", "DevOps", "Automation"],
    "GitLab CI": ["CI/CD", "DevOps"],
    "Jenkins": ["CI/CD", "Build Automation"],
    "CircleCI": ["CI/CD", "DevOps"],
    "Travis CI": ["CI/CD"],
    "Azure DevOps": ["CI/CD", "DevOps"],

    # Containerization
    "Docker": ["Containerization", "DevOps"],
    "Docker Compose": ["Container Orchestration", "Multi-Container Applications"],
    "Kubernetes": ["Container Orchestration", "Cloud-Native"],
    "Helm": ["Kubernetes Package Management"],
    "Podman": ["Containerization"],

    # Infrastructure as Code
    "Terraform": ["Infrastructure as Code", "Cloud Infrastructure"],
    "Pulumi": ["Infrastructure as Code"],
    "AWS CDK": ["Infrastructure as Code", "AWS"],
    "Ansible": ["Configuration Management", "DevOps"],
    "CloudFormation": ["Infrastructure as Code", "AWS"],

    # Testing
    "Jest": ["Unit Testing", "Test-Driven Development"],
    "Vitest": ["Unit Testing", "Fast Testing"],
    "Pytest": ["Unit Testing", "Test-Driven Development"],
    "JUnit": ["Unit Testing", "Java Testing"],
    "Mocha": ["Unit Testing"],
    "Cypress": ["End-to-End Testing", "Test Automation"],
    "Playwright": ["End-to-End Testing", "Cross-Browser Testing"],
    "Selenium": ["Browser Automation", "Test Automation"],
    "Testing Library": ["Component Testing", "User-Centric Testing"],

    # Linting/Formatting
    "ESLint": ["Code Quality", "JavaScript Linting"],
    "Prettier": ["Code Formatting", "Code Quality"],
    "Black": ["Code Formatting", "Python"],
    "Ruff": ["Python Linting", "Code Quality"],
    "Flake8": ["Python Linting"],
    "Pylint": ["Python Linting", "Code Analysis"],
    "Mypy": ["Type Checking", "Python"],
    "TypeScript": ["Type Safety", "Static Typing"],
    "Biome": ["Code Quality", "Fast Linting"],

    # Package Managers
    "npm": ["Package Management", "Node.js"],
    "Yarn": ["Package Management", "Node.js"],
    "pnpm": ["Package Management", "Efficient Dependencies"],
    "Poetry": ["Dependency Management", "Python"],
    "pip": ["Package Management", "Python"],
    "Cargo": ["Package Management", "Rust"],

    # Documentation
    "Storybook": ["Component Documentation", "UI Development"],
    "Swagger": ["API Documentation", "OpenAPI"],
    "Sphinx": ["Documentation Generation", "Python Documentation"],
    "JSDoc": ["JavaScript Documentation"],
    "TypeDoc": ["TypeScript Documentation"],

    # Deployment Platforms
    "Vercel": ["Serverless Deployment", "Frontend Hosting"],
    "Netlify": ["Static Site Hosting", "JAMstack"],
    "Heroku": ["PaaS Deployment", "Cloud Hosting"],
    "Railway": ["Cloud Deployment"],
    "Fly.io": ["Edge Deployment", "Container Hosting"],

    # Monorepo Tools
    "Lerna": ["Monorepo Management"],
    "Nx": ["Monorepo Management", "Build System"],
    "Turborepo": ["Monorepo Management", "Build Caching"],
    "Rush": ["Monorepo Management"],

    # Version Control
    "Git": ["Version Control", "Collaboration"],
    "Git Flow": ["Branching Strategy"],
    "Husky": ["Git Hooks", "Pre-commit Automation"],
    "Commitlint": ["Commit Standards"],

    # Database Tools
    "Prisma": ["ORM", "Database Schema Management"],
    "Alembic": ["Database Migrations", "Schema Management"],
    "Flyway": ["Database Migrations"],
    "Liquibase": ["Database Change Management"],

    # API Development
    "Postman": ["API Testing", "API Development"],
    "Insomnia": ["API Testing"],
    "GraphQL Playground": ["GraphQL Development"],
    "Apollo Studio": ["GraphQL Development", "API Monitoring"],
}


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


def extract_skills_from_libraries(libraries: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract skills from detected libraries.

    Args:
        libraries: List of detected libraries (dicts with name, ecosystem, etc.)

    Returns:
        Set of skills derived from the libraries
    """
    skills = set()

    for lib in libraries:
        lib_name = lib.get("name", "").lower()

        # Check direct mapping
        if lib_name in LIBRARY_SKILLS:
            skills.update(LIBRARY_SKILLS[lib_name])

        # Check partial matches for scoped packages
        for known_lib, lib_skills in LIBRARY_SKILLS.items():
            if known_lib.lower() in lib_name or lib_name in known_lib.lower():
                skills.update(lib_skills)

    # Infer composite skills from library combinations
    lib_names = {lib.get("name", "").lower() for lib in libraries}

    # Data Science stack
    data_libs = {"pandas", "numpy", "scipy", "matplotlib", "seaborn"}
    if len(lib_names & data_libs) >= 3:
        skills.add("Data Science")

    # ML stack
    ml_libs = {"tensorflow", "pytorch", "torch", "keras", "scikit-learn", "sklearn", "transformers"}
    if len(lib_names & ml_libs) >= 2:
        skills.add("Machine Learning Engineering")

    # Web scraping stack
    scraping_libs = {"beautifulsoup4", "scrapy", "selenium", "puppeteer", "cheerio"}
    if len(lib_names & scraping_libs) >= 2:
        skills.add("Web Scraping & Data Extraction")

    # API development stack
    api_libs = {"axios", "requests", "httpx", "aiohttp", "got"}
    if len(lib_names & api_libs) >= 1:
        skills.add("API Integration")

    # Authentication stack
    auth_libs = {"passport", "jsonwebtoken", "bcrypt", "argon2", "pyjwt"}
    if len(lib_names & auth_libs) >= 2:
        skills.add("Authentication & Security")

    # Database stack
    db_libs = {"pg", "mysql2", "mongodb", "pymongo", "psycopg2", "asyncpg", "redis"}
    if len(lib_names & db_libs) >= 1:
        skills.add("Database Integration")

    # Cloud SDK stack
    cloud_libs = {"boto3", "aws-sdk", "google-cloud", "@google-cloud", "azure"}
    if len(lib_names & cloud_libs) >= 1:
        skills.add("Cloud Services Integration")

    return skills


def extract_skills_from_tools(tools: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract skills from detected tools.

    Args:
        tools: List of detected tools (dicts with name, category, etc.)

    Returns:
        Set of skills derived from the tools
    """
    skills = set()

    for tool in tools:
        tool_name = tool.get("name", "")
        category = tool.get("category", "")

        # Check direct mapping
        if tool_name in TOOL_SKILLS:
            skills.update(TOOL_SKILLS[tool_name])

        # Category-based skills
        if category == "cicd":
            skills.add("CI/CD Pipeline Configuration")
        elif category == "container":
            skills.add("Containerization")
        elif category == "infrastructure":
            skills.add("Infrastructure as Code")
        elif category == "testing":
            skills.add("Test Automation")
        elif category == "linting":
            skills.add("Code Quality & Standards")

    # Infer composite skills from tool combinations
    tool_names = {tool.get("name", "") for tool in tools}
    tool_categories = {tool.get("category", "") for tool in tools}

    # DevOps stack
    devops_tools = {"Docker", "Kubernetes", "GitHub Actions", "GitLab CI", "Jenkins", "Terraform", "Ansible"}
    if len(tool_names & devops_tools) >= 3:
        skills.add("DevOps & Infrastructure")

    # Full CI/CD setup
    if "cicd" in tool_categories and "container" in tool_categories:
        skills.add("CI/CD Pipeline Management")

    # Testing expertise
    testing_tools = {"Jest", "Pytest", "Cypress", "Playwright", "Vitest", "JUnit"}
    if len(tool_names & testing_tools) >= 2:
        skills.add("Comprehensive Testing Strategy")

    # Code quality
    quality_tools = {"ESLint", "Prettier", "Black", "Ruff", "Mypy", "TypeScript"}
    if len(tool_names & quality_tools) >= 2:
        skills.add("Code Quality Automation")

    # Modern frontend tooling
    frontend_tools = {"Vite", "Webpack", "esbuild", "Turbopack", "Rollup"}
    if len(tool_names & frontend_tools) >= 1:
        skills.add("Modern Build Systems")

    # Documentation tools
    doc_tools = {"Storybook", "Swagger", "Sphinx", "JSDoc", "TypeDoc"}
    if len(tool_names & doc_tools) >= 1:
        skills.add("Technical Documentation")

    # Monorepo management
    monorepo_tools = {"Lerna", "Nx", "Turborepo", "Rush"}
    if len(tool_names & monorepo_tools) >= 1:
        skills.add("Monorepo Architecture")

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


def _infer_contextual_skills(
    languages: List[str],
    frameworks: List[str],
    libraries: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Set[str]:
    """
    Infer contextual skills based on language + framework + library + tool combinations.

    This enhanced version considers all four detection signals to provide
    richer skill inference based on multi-signal agreement.

    Args:
        languages: List of detected languages
        frameworks: List of detected frameworks
        libraries: Optional list of detected libraries
        tools: Optional list of detected tools

    Returns:
        Set of inferred contextual skills
    """
    skills = set()
    lang_set = set(languages)
    framework_set = set(frameworks)

    # Extract library and tool names for easier checking
    lib_names = set()
    if libraries:
        lib_names = {lib.get("name", "").lower() for lib in libraries}

    tool_names = set()
    tool_categories = set()
    if tools:
        tool_names = {tool.get("name", "") for tool in tools}
        tool_categories = {tool.get("category", "") for tool in tools}

    # =========================================================================
    # Backend vs Frontend Detection
    # =========================================================================
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

    has_backend = bool(lang_set & backend_langs) or bool(framework_set & backend_frameworks)
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

    # =========================================================================
    # Mobile Development
    # =========================================================================
    mobile_frameworks = {"React Native", "Expo", "Ionic", "NativeScript", "Flutter"}

    if "Swift" in lang_set:
        skills.add("Mobile Development")

    if "Dart" in lang_set and "Flutter" in framework_set:
        skills.add("Mobile Development")

    if (lang_set & frontend_langs) and (framework_set & mobile_frameworks):
        skills.add("Mobile Development")

    # =========================================================================
    # Data Science & ML (enhanced with library detection)
    # =========================================================================
    if "Python" in lang_set:
        data_frameworks = {"Pandas", "NumPy", "Scikit-learn", "Jupyter Notebook"}
        data_libs = {"pandas", "numpy", "scipy", "matplotlib", "seaborn", "polars"}

        if (framework_set & data_frameworks) or len(lib_names & data_libs) >= 2:
            skills.add("Data Science")

    if "R" in lang_set:
        skills.add("Data Science")

    ml_frameworks = {"TensorFlow", "PyTorch", "Keras", "Scikit-learn"}
    ml_libs = {"tensorflow", "pytorch", "torch", "keras", "scikit-learn", "sklearn", "transformers", "huggingface"}

    if (framework_set & ml_frameworks) or len(lib_names & ml_libs) >= 2:
        skills.add("Machine Learning")

    # NLP specialization
    nlp_libs = {"transformers", "spacy", "nltk", "gensim", "huggingface"}
    if len(lib_names & nlp_libs) >= 2:
        skills.add("Natural Language Processing")

    # =========================================================================
    # DevOps & Infrastructure (enhanced with tool detection)
    # =========================================================================
    has_containers = "Docker" in framework_set or "Docker" in tool_names
    has_scripting = lang_set & {"Shell", "PowerShell", "Batch"}
    has_cicd = "cicd" in tool_categories
    has_k8s = "Kubernetes" in tool_names or "kubernetes" in lib_names

    if has_containers and has_scripting:
        skills.add("DevOps")

    if has_containers and has_cicd:
        skills.add("DevOps")
        skills.add("CI/CD Pipeline Management")

    if has_k8s:
        skills.add("Container Orchestration")
        skills.add("Cloud-Native Development")

    # Infrastructure as Code
    iac_tools = {"Terraform", "Pulumi", "AWS CDK", "Ansible", "CloudFormation"}
    if tool_names & iac_tools:
        skills.add("Infrastructure as Code")

    # =========================================================================
    # Modern Frontend Development (enhanced)
    # =========================================================================
    modern_build_tools = {"Vite", "Webpack", "esbuild", "Turbopack"}
    testing_tools = {"Jest", "Vitest", "Cypress", "Playwright"}
    ui_frameworks = {"React", "Vue", "Angular", "Svelte", "Next.js"}

    if (framework_set & ui_frameworks) and (tool_names & modern_build_tools) and (tool_names & testing_tools):
        skills.add("Modern Frontend Development")

    # =========================================================================
    # Full-Stack Web Development (enhanced with DB detection)
    # =========================================================================
    db_libs = {"pg", "mysql2", "mongodb", "pymongo", "psycopg2", "asyncpg", "prisma", "sequelize", "typeorm"}
    has_db = len(lib_names & db_libs) >= 1

    if has_backend and has_frontend and has_db:
        skills.add("Full-Stack Web Development")

    # =========================================================================
    # API Development
    # =========================================================================
    api_frameworks = {"FastAPI", "Express", "Flask", "Django", "NestJS"}
    api_tools = {"Swagger", "Postman", "Insomnia"}
    graphql_indicators = {"graphql", "apollo", "@apollo/client", "apollo-server"}

    if (framework_set & api_frameworks) and (tool_names & api_tools):
        skills.add("API Design & Development")

    if lib_names & graphql_indicators or "GraphQL" in framework_set:
        skills.add("GraphQL Development")

    # =========================================================================
    # Real-Time Applications
    # =========================================================================
    realtime_libs = {"socket.io", "ws", "websockets", "pusher"}
    if lib_names & realtime_libs:
        skills.add("Real-Time Applications")

    # =========================================================================
    # Microservices Architecture
    # =========================================================================
    microservice_indicators = {
        "has_docker": has_containers,
        "has_k8s": has_k8s,
        "has_message_queue": bool(lib_names & {"amqplib", "bull", "celery", "kafka-python"}),
        "has_api_gateway": bool(lib_names & {"express-gateway", "kong"}),
    }
    if sum(microservice_indicators.values()) >= 3:
        skills.add("Microservices Architecture")

    # =========================================================================
    # Security-focused Development
    # =========================================================================
    security_libs = {"bcrypt", "argon2", "jsonwebtoken", "pyjwt", "passport", "helmet"}
    if len(lib_names & security_libs) >= 2:
        skills.add("Security-Focused Development")

    # =========================================================================
    # Performance Optimization
    # =========================================================================
    perf_libs = {"redis", "memcached", "sharp", "imagemin"}
    perf_tools = {"Webpack", "Vite", "esbuild"}
    if (lib_names & perf_libs) and (tool_names & perf_tools):
        skills.add("Performance Optimization")

    return skills


def extract_resume_skills(
    root_dir: Union[str, Path],
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    libraries: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    include_code_patterns: bool = False,
) -> List[str]:
    """
    Extract comprehensive resume-ready skills from a project.

    Args:
        root_dir: Path to the project directory
        languages: Optional pre-detected list of languages
        frameworks: Optional pre-detected list of frameworks
        libraries: Optional pre-detected list of libraries
        tools: Optional pre-detected list of tools
        include_code_patterns: If True, also run regex-based code pattern analysis

    Returns:
        Sorted list of unique skills
    """
    root_path = Path(root_dir)
    all_skills: Set[str] = set()

    # Get languages if not provided
    if languages is None:
        from src.core.detectors.language import ProjectAnalyzer
        analyzer = ProjectAnalyzer()
        language_stats = analyzer.analyze_project_languages(str(root_path))
        languages = [lang for lang, count in language_stats.items() if lang != "Unknown" and count > 0]

    # Get frameworks if not provided
    if frameworks is None:
        from src.core.detectors.framework import detect_frameworks_recursive
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

    # Extract skills from libraries and tools if provided
    if libraries:
        all_skills.update(extract_skills_from_libraries(libraries))
    if tools:
        all_skills.update(extract_skills_from_tools(tools))

    # Use enhanced contextual inference with libraries and tools
    all_skills.update(_infer_contextual_skills(languages, frameworks, libraries, tools))

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
    libraries: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    include_code_patterns: bool = False,
) -> Dict[str, Any]:
    """
    Comprehensive project skill analysis with source tracking.

    Args:
        root_dir: Path to the project directory
        libraries: Optional pre-detected list of libraries
        tools: Optional pre-detected list of tools
        languages: Optional pre-detected list of languages (skip detection if provided)
        frameworks: Optional pre-detected list of frameworks (skip detection if provided)
        include_code_patterns: If True, also run regex-based code pattern analysis

    Returns:
        Dictionary containing languages, frameworks, skills, skill categories,
        and skill_sources mapping each skill to its detection source
    """
    root_path = Path(root_dir)

    # Extract languages (or use provided)
    if languages is None:
        from src.core.detectors.language import ProjectAnalyzer
        analyzer = ProjectAnalyzer()
        language_stats = analyzer.analyze_project_languages(str(root_path))
        languages = [lang for lang, count in language_stats.items() if lang != "Unknown" and count > 0]

    # Extract frameworks (or use provided)
    if frameworks is None:
        from src.core.detectors.framework import detect_frameworks_recursive
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

    # Extract skills from each source separately for tracking
    skill_sources: Dict[str, str] = {}  # Maps skill name -> source

    # Skills from languages
    lang_skills = extract_skills_from_languages(languages)
    for skill in lang_skills:
        skill_sources[skill] = "language"

    # Skills from frameworks
    fw_skills = extract_skills_from_frameworks(frameworks)
    for skill in fw_skills:
        if skill not in skill_sources:  # Don't overwrite if already set
            skill_sources[skill] = "framework"

    # Skills from file types
    file_skills = extract_skills_from_files(root_path)
    for skill in file_skills:
        if skill not in skill_sources:
            skill_sources[skill] = "file_type"

    # Skills from libraries
    if libraries:
        lib_skills = extract_skills_from_libraries(libraries)
        for skill in lib_skills:
            if skill not in skill_sources:
                skill_sources[skill] = "library"

    # Skills from tools
    if tools:
        tool_skills = extract_skills_from_tools(tools)
        for skill in tool_skills:
            if skill not in skill_sources:
                skill_sources[skill] = "tool"

    # Contextual skills (inferred from combinations)
    contextual_skills = _infer_contextual_skills(languages, frameworks, libraries, tools)
    for skill in contextual_skills:
        if skill not in skill_sources:
            skill_sources[skill] = "contextual"

    # All unique skills
    all_skills = sorted(skill_sources.keys())

    # Categorize skills
    categories = get_skill_categories()
    categorized_skills: Dict[str, List[str]] = {}

    for skill in all_skills:
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
        "skills": all_skills,
        "skill_categories": categorized_skills,
        "skill_sources": skill_sources,  # New: maps skill -> source
        "total_skills": len(all_skills),
        "project_path": str(root_path.resolve()),
    }
