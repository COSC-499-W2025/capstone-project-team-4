"""
Skill Extraction Module

Extracts professional skills from detected languages, frameworks, libraries,
tools, and file types in a project. Skill mappings are loaded from YAML
configuration for easy maintenance.

Main functions:
    - analyze_project_skills(): Comprehensive project skill analysis
    - extract_resume_skills(): Extract all skills from a project
    - extract_skills_from_languages(): Get skills from programming languages
    - extract_skills_from_frameworks(): Get skills from frameworks/libraries
    - extract_skills_from_files(): Get skills from file types
    - analyze_code_patterns(): Regex-based skill detection from code
"""

import json
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any

import yaml

from src.core.constants import SKIP_DIRECTORIES

logger = logging.getLogger(__name__)

# Path to skills configuration
SKILLS_YAML_PATH = Path(__file__).parent.parent / "rules" / "skills.yml"


@lru_cache(maxsize=1)
def _load_skills_config() -> Dict[str, Any]:
    """Load and cache skills configuration from YAML."""
    if not SKILLS_YAML_PATH.exists():
        logger.warning("Skills config not found at %s, using empty config", SKILLS_YAML_PATH)
        return {}

    with open(SKILLS_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_skill_mapping(key: str) -> Dict[str, List[str]]:
    """Get a skill mapping dict from config, with empty fallback."""
    config = _load_skills_config()
    return config.get(key, {})


# Lazy-loaded skill mappings from YAML
def _get_language_skills() -> Dict[str, List[str]]:
    return _get_skill_mapping("language_skills")


def _get_framework_skills() -> Dict[str, List[str]]:
    return _get_skill_mapping("framework_skills")


def _get_library_skills() -> Dict[str, List[str]]:
    return _get_skill_mapping("library_skills")


def _get_tool_skills() -> Dict[str, List[str]]:
    return _get_skill_mapping("tool_skills")


def _get_file_type_skills() -> Dict[str, List[str]]:
    return _get_skill_mapping("file_type_skills")


def _get_composite_rules() -> Dict[str, List[Dict]]:
    """Get composite skill rules from config."""
    config = _load_skills_config()
    return config.get("composite_rules", {})


def _get_tool_category_skills() -> Dict[str, str]:
    """Get tool category to skill mapping."""
    config = _load_skills_config()
    return config.get("tool_category_skills", {})


def _get_file_threshold_rules() -> List[Dict]:
    """Get file-based threshold rules."""
    config = _load_skills_config()
    return config.get("file_threshold_rules", [])


def _get_single_file_triggers() -> List[str]:
    """Get extensions that trigger skills with just 1 file."""
    config = _load_skills_config()
    return config.get("single_file_triggers", [])


# =============================================================================
# Regex-based code pattern detection
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

def _count_skills(mapping: Dict[str, List[str]], items: List[str]) -> Counter:
    """
    Helper to count skills from a mapping dict.

    Args:
        mapping: Dict mapping item names to lists of skills
        items: List of detected items (languages, frameworks, etc.)

    Returns:
        Counter of skill occurrences
    """
    counts: Counter = Counter()
    for item in items:
        if item in mapping:
            counts.update(mapping[item])
    return counts


def extract_skills_from_languages(languages: List[str]) -> Dict[str, int]:
    """
    Extract skills from detected programming languages with frequency counts.

    Args:
        languages: List of detected programming languages

    Returns:
        Dict mapping skill names to their occurrence counts
    """
    counts = _count_skills(_get_language_skills(), languages)

    # Web Design skill when HTML + CSS are detected together
    if "HTML" in languages and "CSS" in languages:
        counts["Web Design"] += 1

    return dict(counts)


def extract_skills_from_frameworks(frameworks: List[str]) -> Dict[str, int]:
    """
    Extract skills from detected frameworks and libraries with frequency counts.

    Args:
        frameworks: List of detected frameworks

    Returns:
        Dict mapping skill names to their occurrence counts
    """
    counts = _count_skills(_get_framework_skills(), frameworks)
    framework_set = set(frameworks)

    # Apply composite rules from YAML
    composite_rules = _get_composite_rules().get("frameworks", [])
    for rule in composite_rules:
        skill = rule.get("skill", "")
        requires = set(rule.get("requires", []))
        min_count = rule.get("min_count", 1)

        match_count = len(framework_set & requires)
        if match_count >= min_count:
            counts[skill] += match_count

    return dict(counts)


def extract_skills_from_libraries(libraries: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract skills from detected libraries with frequency counts.

    Args:
        libraries: List of detected libraries (dicts with name, ecosystem, etc.)

    Returns:
        Dict mapping skill names to their occurrence counts
    """
    counts: Counter = Counter()
    lib_names_lower = []
    library_skills = _get_library_skills()

    for lib in libraries:
        lib_name = lib.get("name", "").lower()
        lib_names_lower.append(lib_name)

        # Check direct mapping
        if lib_name in library_skills:
            counts.update(library_skills[lib_name])

        # Check partial matches for scoped packages
        for known_lib, lib_skills in library_skills.items():
            if known_lib.lower() in lib_name or lib_name in known_lib.lower():
                counts.update(lib_skills)

    lib_names = set(lib_names_lower)

    # Apply composite rules from YAML
    composite_rules = _get_composite_rules().get("libraries", [])
    for rule in composite_rules:
        skill = rule.get("skill", "")
        requires = set(rule.get("requires", []))
        min_count = rule.get("min_count", 1)

        match_count = len(lib_names & requires)
        if match_count >= min_count:
            counts[skill] += match_count

    return dict(counts)


def extract_skills_from_tools(tools: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract skills from detected tools with frequency counts.

    Args:
        tools: List of detected tools (dicts with name, category, etc.)

    Returns:
        Dict mapping skill names to their occurrence counts
    """
    counts: Counter = Counter()
    tool_names = set()
    tool_categories = set()

    tool_skills = _get_tool_skills()
    category_skills = _get_tool_category_skills()

    for tool in tools:
        tool_name = tool.get("name", "")
        category = tool.get("category", "")
        tool_names.add(tool_name)
        tool_categories.add(category)

        # Check direct mapping
        if tool_name in tool_skills:
            counts.update(tool_skills[tool_name])

        # Category-based skills
        if category in category_skills:
            counts[category_skills[category]] += 1

    # Apply composite rules from YAML
    composite_rules = _get_composite_rules().get("tools", [])
    for rule in composite_rules:
        skill = rule.get("skill", "")
        requires = set(rule.get("requires", []))
        min_count = rule.get("min_count", 1)

        match_count = len(tool_names & requires)
        if match_count >= min_count:
            counts[skill] += match_count

    # Full CI/CD setup
    if "cicd" in tool_categories and "container" in tool_categories:
        counts["CI/CD Pipeline Management"] += 1

    return dict(counts)


def extract_skills_from_files(root_dir: Union[str, Path]) -> Dict[str, int]:
    """
    Extract skills from file types in a project with frequency counts.

    Args:
        root_dir: Path to the project directory

    Returns:
        Dict mapping skill names to their occurrence counts
    """
    root_path = Path(root_dir)
    counts: Counter = Counter()
    file_counter: Counter = Counter()

    file_type_skills = _get_file_type_skills()

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRECTORIES]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()

            if filename.lower() in file_type_skills:
                counts.update(file_type_skills[filename.lower()])

            if ext in file_type_skills:
                file_counter[ext] += 1

    # Apply threshold rules from YAML
    threshold_rules = _get_file_threshold_rules()
    for rule in threshold_rules:
        skills = rule.get("skills", [])
        exts = set(rule.get("extensions", []))
        min_count = rule.get("min_count", 1)

        ext_count = sum(file_counter.get(ext, 0) for ext in exts)
        if ext_count >= min_count:
            for skill in skills:
                counts[skill] += ext_count

    # Single-file triggers from YAML
    single_file_exts = _get_single_file_triggers()
    for ext in single_file_exts:
        ext_count = file_counter.get(ext, 0)
        if ext_count >= 1 and ext in file_type_skills:
            for skill in file_type_skills[ext]:
                counts[skill] += ext_count

    return dict(counts)


def _infer_contextual_skills(
    languages: List[str],
    frameworks: List[str],
    libraries: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, int]:
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
        Dict mapping skill names to their occurrence counts (based on contributing signals)
    """
    skill_counts: Dict[str, int] = {}
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

    backend_lang_count = len(lang_set & backend_langs)
    backend_fw_count = len(framework_set & backend_frameworks)
    frontend_lang_count = len(lang_set & frontend_langs)
    frontend_fw_count = len(framework_set & frontend_frameworks)

    has_backend = backend_lang_count > 0 or backend_fw_count > 0
    has_modern_frontend = frontend_lang_count > 0 and frontend_fw_count > 0
    has_traditional_frontend = ("HTML" in lang_set) or ("CSS" in lang_set)
    has_frontend = has_modern_frontend or has_traditional_frontend

    if has_backend and has_frontend:
        # Count contributing signals
        signal_count = backend_lang_count + backend_fw_count + frontend_lang_count + frontend_fw_count
        skill_counts["Full-Stack Development"] = signal_count
    else:
        if has_backend:
            skill_counts["Backend Development"] = backend_lang_count + backend_fw_count
        if has_modern_frontend:
            skill_counts["Frontend Development"] = frontend_lang_count + frontend_fw_count
        elif has_traditional_frontend and not has_backend:
            skill_counts["Frontend Development"] = 1

    # =========================================================================
    # Mobile Development
    # =========================================================================
    mobile_frameworks = {"React Native", "Expo", "Ionic", "NativeScript", "Flutter"}
    mobile_signals = 0

    if "Swift" in lang_set:
        mobile_signals += 1

    if "Dart" in lang_set and "Flutter" in framework_set:
        mobile_signals += 2

    mobile_fw_count = len(framework_set & mobile_frameworks)
    if (lang_set & frontend_langs) and mobile_fw_count > 0:
        mobile_signals += mobile_fw_count

    if mobile_signals > 0:
        skill_counts["Mobile Development"] = mobile_signals

    # =========================================================================
    # Data Science & ML (enhanced with library detection)
    # =========================================================================
    data_signals = 0
    if "Python" in lang_set:
        data_frameworks = {"Pandas", "NumPy", "Scikit-learn", "Jupyter Notebook"}
        data_libs = {"pandas", "numpy", "scipy", "matplotlib", "seaborn", "polars"}

        data_fw_count = len(framework_set & data_frameworks)
        data_lib_count = len(lib_names & data_libs)

        if data_fw_count > 0 or data_lib_count >= 2:
            data_signals = data_fw_count + data_lib_count

    if "R" in lang_set:
        data_signals += 1

    if data_signals > 0:
        skill_counts["Data Science"] = data_signals

    ml_frameworks = {"TensorFlow", "PyTorch", "Keras", "Scikit-learn"}
    ml_libs = {"tensorflow", "pytorch", "torch", "keras", "scikit-learn", "sklearn", "transformers", "huggingface"}

    ml_fw_count = len(framework_set & ml_frameworks)
    ml_lib_count = len(lib_names & ml_libs)

    if ml_fw_count > 0 or ml_lib_count >= 2:
        skill_counts["Machine Learning"] = ml_fw_count + ml_lib_count

    # NLP specialization
    nlp_libs = {"transformers", "spacy", "nltk", "gensim", "huggingface"}
    nlp_count = len(lib_names & nlp_libs)
    if nlp_count >= 2:
        skill_counts["Natural Language Processing"] = nlp_count

    # =========================================================================
    # DevOps & Infrastructure (enhanced with tool detection)
    # =========================================================================
    has_containers = "Docker" in framework_set or "Docker" in tool_names
    scripting_count = len(lang_set & {"Shell", "PowerShell", "Batch"})
    has_cicd = "cicd" in tool_categories
    has_k8s = "Kubernetes" in tool_names or "kubernetes" in lib_names

    if has_containers and scripting_count > 0:
        skill_counts["DevOps"] = skill_counts.get("DevOps", 0) + 1 + scripting_count

    if has_containers and has_cicd:
        skill_counts["DevOps"] = skill_counts.get("DevOps", 0) + 2
        skill_counts["CI/CD Pipeline Management"] = skill_counts.get("CI/CD Pipeline Management", 0) + 2

    if has_k8s:
        skill_counts["Container Orchestration"] = skill_counts.get("Container Orchestration", 0) + 1
        skill_counts["Cloud-Native Development"] = skill_counts.get("Cloud-Native Development", 0) + 1

    # Infrastructure as Code
    iac_tools = {"Terraform", "Pulumi", "AWS CDK", "Ansible", "CloudFormation"}
    iac_count = len(tool_names & iac_tools)
    if iac_count > 0:
        skill_counts["Infrastructure as Code"] = iac_count

    # =========================================================================
    # Modern Frontend Development (enhanced)
    # =========================================================================
    modern_build_tools = {"Vite", "Webpack", "esbuild", "Turbopack"}
    testing_tools = {"Jest", "Vitest", "Cypress", "Playwright"}
    ui_frameworks = {"React", "Vue", "Angular", "Svelte", "Next.js"}

    ui_count = len(framework_set & ui_frameworks)
    build_count = len(tool_names & modern_build_tools)
    test_count = len(tool_names & testing_tools)

    if ui_count > 0 and build_count > 0 and test_count > 0:
        skill_counts["Modern Frontend Development"] = ui_count + build_count + test_count

    # =========================================================================
    # Full-Stack Web Development (enhanced with DB detection)
    # =========================================================================
    db_libs = {"pg", "mysql2", "mongodb", "pymongo", "psycopg2", "asyncpg", "prisma", "sequelize", "typeorm"}
    db_count = len(lib_names & db_libs)

    if has_backend and has_frontend and db_count >= 1:
        skill_counts["Full-Stack Web Development"] = skill_counts.get("Full-Stack Development", 1) + db_count

    # =========================================================================
    # API Development
    # =========================================================================
    api_frameworks = {"FastAPI", "Express", "Flask", "Django", "NestJS"}
    api_tools = {"Swagger", "Postman", "Insomnia"}
    graphql_indicators = {"graphql", "apollo", "@apollo/client", "apollo-server"}

    api_fw_count = len(framework_set & api_frameworks)
    api_tool_count = len(tool_names & api_tools)

    if api_fw_count > 0 and api_tool_count > 0:
        skill_counts["API Design & Development"] = api_fw_count + api_tool_count

    graphql_count = len(lib_names & graphql_indicators)
    if graphql_count > 0 or "GraphQL" in framework_set:
        skill_counts["GraphQL Development"] = graphql_count + (1 if "GraphQL" in framework_set else 0)

    # =========================================================================
    # Real-Time Applications
    # =========================================================================
    realtime_libs = {"socket.io", "ws", "websockets", "pusher"}
    realtime_count = len(lib_names & realtime_libs)
    if realtime_count > 0:
        skill_counts["Real-Time Applications"] = realtime_count

    # =========================================================================
    # Microservices Architecture
    # =========================================================================
    mq_count = len(lib_names & {"amqplib", "bull", "celery", "kafka-python"})
    gateway_count = len(lib_names & {"express-gateway", "kong"})

    microservice_signals = sum([
        1 if has_containers else 0,
        1 if has_k8s else 0,
        mq_count,
        gateway_count,
    ])
    if microservice_signals >= 3:
        skill_counts["Microservices Architecture"] = microservice_signals

    # =========================================================================
    # Security-focused Development
    # =========================================================================
    security_libs = {"bcrypt", "argon2", "jsonwebtoken", "pyjwt", "passport", "helmet"}
    security_count = len(lib_names & security_libs)
    if security_count >= 2:
        skill_counts["Security-Focused Development"] = security_count

    # =========================================================================
    # Performance Optimization
    # =========================================================================
    perf_libs = {"redis", "memcached", "sharp", "imagemin"}
    perf_tools = {"Webpack", "Vite", "esbuild"}

    perf_lib_count = len(lib_names & perf_libs)
    perf_tool_count = len(tool_names & perf_tools)

    if perf_lib_count > 0 and perf_tool_count > 0:
        skill_counts["Performance Optimization"] = perf_lib_count + perf_tool_count

    return skill_counts


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

    # Extraction functions now return Dict[str, int], use .keys() for skill names
    all_skills.update(extract_skills_from_languages(languages).keys())
    all_skills.update(extract_skills_from_frameworks(frameworks).keys())
    all_skills.update(extract_skills_from_files(root_path).keys())

    # Extract skills from libraries and tools if provided
    if libraries:
        all_skills.update(extract_skills_from_libraries(libraries).keys())
    if tools:
        all_skills.update(extract_skills_from_tools(tools).keys())

    # Use enhanced contextual inference with libraries and tools
    all_skills.update(_infer_contextual_skills(languages, frameworks, libraries, tools).keys())

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

    for skills in _get_language_skills().values():
        for skill in skills:
            if any(keyword in skill for keyword in ["Programming", "Development", "Scripting"]):
                categories["Programming Languages"].add(skill)

    for skills in _get_framework_skills().values():
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

    for skills in _get_file_type_skills().values():
        for skill in skills:
            if any(keyword in skill for keyword in ["Design", "Photo", "Video", "Audio", "3D", "Graphics"]):
                categories["Design & Creative"].add(skill)

    # Add library skills to categories
    for skills in _get_library_skills().values():
        for skill in skills:
            if any(keyword in skill for keyword in ["Machine Learning", "Data Science", "AI", "Deep Learning", "NLP", "Natural Language", "Data Analysis", "Data Processing", "Scientific Computing", "Statistical", "Computer Vision"]):
                categories["Data Science & ML"].add(skill)
            elif any(keyword in skill for keyword in ["Database", "SQL", "PostgreSQL", "MySQL", "MongoDB", "NoSQL", "Redis", "Caching", "ORM"]):
                categories["Database & ORM"].add(skill)
            elif any(keyword in skill for keyword in ["DevOps", "Docker", "CI/CD", "Container", "Cloud", "AWS", "Azure", "Google Cloud", "Infrastructure", "Monitoring", "Metrics"]):
                categories["DevOps & Infrastructure"].add(skill)
            elif any(keyword in skill for keyword in ["Testing", "Test-Driven", "QA", "Quality"]):
                categories["Testing & QA"].add(skill)
            elif any(keyword in skill for keyword in ["Frontend", "Backend", "Web", "API", "HTTP", "REST", "WebSocket", "Real-Time", "Authentication", "OAuth", "JWT", "Security"]):
                categories["Web Development"].add(skill)
            elif any(keyword in skill for keyword in ["Mobile", "iOS", "Android"]):
                categories["Mobile Development"].add(skill)
            elif any(keyword in skill for keyword in ["Design", "Photo", "Video", "Audio", "3D", "Graphics", "Image"]):
                categories["Design & Creative"].add(skill)

    # Add tool skills to categories
    for skills in _get_tool_skills().values():
        for skill in skills:
            if any(keyword in skill for keyword in ["DevOps", "Docker", "CI/CD", "Container", "Containerization", "Orchestration", "Infrastructure", "Cloud", "Deployment", "Hosting", "Serverless"]):
                categories["DevOps & Infrastructure"].add(skill)
            elif any(keyword in skill for keyword in ["Testing", "Test", "QA", "Quality", "Linting", "Code Quality", "Formatting", "Type Checking", "Type Safety"]):
                categories["Testing & QA"].add(skill)
            elif any(keyword in skill for keyword in ["Database", "ORM", "Migration", "Schema"]):
                categories["Database & ORM"].add(skill)
            elif any(keyword in skill for keyword in ["API", "REST", "GraphQL", "Documentation"]):
                categories["Web Development"].add(skill)
            elif any(keyword in skill for keyword in ["Build", "Bundling", "Package", "Monorepo", "Version Control"]):
                categories["DevOps & Infrastructure"].add(skill)

    return {k: sorted(list(v)) for k, v in categories.items() if v}


def categorize_skill_by_keywords(skill: str) -> Optional[str]:
    """
    Categorize a skill by keyword matching.
    Returns the category name or None if no match.
    """
    skill_lower = skill.lower()

    # Data Science & ML keywords
    if any(kw in skill_lower for kw in [
        "machine learning", "data science", "ai", "deep learning", "nlp",
        "natural language", "data analysis", "data processing", "scientific",
        "statistical", "computer vision", "data manipulation", "numerical",
        "neural", "model", "training", "prediction", "classification"
    ]):
        return "Data Science & ML"

    # DevOps & Infrastructure keywords
    if any(kw in skill_lower for kw in [
        "devops", "docker", "ci/cd", "container", "cloud", "aws", "azure",
        "google cloud", "infrastructure", "monitoring", "metrics", "deployment",
        "hosting", "serverless", "orchestration", "pipeline", "automation",
        "kubernetes", "terraform", "ansible", "build", "bundling", "package",
        "monorepo", "version control", "git"
    ]):
        return "DevOps & Infrastructure"

    # Testing & QA keywords
    if any(kw in skill_lower for kw in [
        "testing", "test-driven", "test driven", "qa", "quality", "linting",
        "code quality", "formatting", "type checking", "type safety", "unit test",
        "integration test", "e2e", "end-to-end", "coverage"
    ]):
        return "Testing & QA"

    # Database & ORM keywords
    if any(kw in skill_lower for kw in [
        "database", "sql", "postgresql", "mysql", "mongodb", "nosql", "redis",
        "caching", "orm", "migration", "schema", "query"
    ]):
        return "Database & ORM"

    # Web Development keywords
    if any(kw in skill_lower for kw in [
        "frontend", "backend", "web", "api", "http", "rest", "websocket",
        "real-time", "authentication", "oauth", "jwt", "security", "graphql",
        "fullstack", "full-stack", "full stack", "component", "spa", "ssr",
        "async", "server", "client", "request", "response"
    ]):
        return "Web Development"

    # Mobile Development keywords
    if any(kw in skill_lower for kw in [
        "mobile", "ios", "android", "react native", "flutter", "swift", "kotlin"
    ]):
        return "Mobile Development"

    # Design & Creative keywords
    if any(kw in skill_lower for kw in [
        "design", "photo", "video", "audio", "3d", "graphics", "image",
        "ui", "ux", "animation", "illustration"
    ]):
        return "Design & Creative"

    # Programming Languages keywords
    if any(kw in skill_lower for kw in [
        "programming", "development language", "scripting"
    ]):
        return "Programming Languages"

    return None


def analyze_project_skills(
    root_dir: Union[str, Path],
    libraries: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    include_code_patterns: bool = False,
) -> Dict[str, Any]:
    """
    Comprehensive project skill analysis with source tracking and frequency counts.

    Args:
        root_dir: Path to the project directory
        libraries: Optional pre-detected list of libraries
        tools: Optional pre-detected list of tools
        languages: Optional pre-detected list of languages (skip detection if provided)
        frameworks: Optional pre-detected list of frameworks (skip detection if provided)
        include_code_patterns: If True, also run regex-based code pattern analysis

    Returns:
        Dictionary containing languages, frameworks, skills, skill categories,
        skill_sources mapping each skill to its detection source, and
        skill_frequencies mapping each skill to its occurrence count
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
    skill_frequencies: Dict[str, int] = {}  # Maps skill name -> occurrence count

    # Skills from languages (returns Dict[str, int])
    lang_skills = extract_skills_from_languages(languages)
    for skill, count in lang_skills.items():
        skill_frequencies[skill] = skill_frequencies.get(skill, 0) + count
        if skill not in skill_sources:
            skill_sources[skill] = "language"

    # Skills from frameworks (returns Dict[str, int])
    fw_skills = extract_skills_from_frameworks(frameworks)
    for skill, count in fw_skills.items():
        skill_frequencies[skill] = skill_frequencies.get(skill, 0) + count
        if skill not in skill_sources:
            skill_sources[skill] = "framework"

    # Skills from file types (returns Dict[str, int])
    file_skills = extract_skills_from_files(root_path)
    for skill, count in file_skills.items():
        skill_frequencies[skill] = skill_frequencies.get(skill, 0) + count
        if skill not in skill_sources:
            skill_sources[skill] = "file_type"

    # Skills from libraries (returns Dict[str, int])
    if libraries:
        lib_skills = extract_skills_from_libraries(libraries)
        for skill, count in lib_skills.items():
            skill_frequencies[skill] = skill_frequencies.get(skill, 0) + count
            if skill not in skill_sources:
                skill_sources[skill] = "library"

    # Skills from tools (returns Dict[str, int])
    if tools:
        tool_skills = extract_skills_from_tools(tools)
        for skill, count in tool_skills.items():
            skill_frequencies[skill] = skill_frequencies.get(skill, 0) + count
            if skill not in skill_sources:
                skill_sources[skill] = "tool"

    # Contextual skills (inferred from combinations, returns Dict[str, int])
    contextual_skills = _infer_contextual_skills(languages, frameworks, libraries, tools)
    for skill, count in contextual_skills.items():
        skill_frequencies[skill] = skill_frequencies.get(skill, 0) + count
        if skill not in skill_sources:
            skill_sources[skill] = "contextual"

    # All unique skills
    all_skills = sorted(skill_sources.keys())

    # Categorize skills
    categories = get_skill_categories()
    categorized_skills: Dict[str, List[str]] = {}

    for skill in all_skills:
        placed = False
        # First try exact match from predefined categories
        for category, category_skills in categories.items():
            if skill in category_skills:
                if category not in categorized_skills:
                    categorized_skills[category] = []
                categorized_skills[category].append(skill)
                placed = True
                break

        # If not found, try keyword-based categorization
        if not placed:
            keyword_category = categorize_skill_by_keywords(skill)
            if keyword_category:
                if keyword_category not in categorized_skills:
                    categorized_skills[keyword_category] = []
                categorized_skills[keyword_category].append(skill)
                placed = True

        # Fall back to "Other" only if no match found
        if not placed:
            if "Other" not in categorized_skills:
                categorized_skills["Other"] = []
            categorized_skills["Other"].append(skill)

    return {
        "languages": languages,
        "frameworks": frameworks,
        "skills": all_skills,
        "skill_categories": categorized_skills,
        "skill_sources": skill_sources,  # Maps skill -> source
        "skill_frequencies": skill_frequencies,  # Maps skill -> occurrence count
        "total_skills": len(all_skills),
        "project_path": str(root_path.resolve()),
    }
