"""
Skill Extraction Module

This module extracts professional skills from detected languages, frameworks,
and file types in a project. It provides intelligent skill inference that goes
beyond simple detection to understand what capabilities are demonstrated.

Main functions:
    - extract_skills(): Extract all skills from a project
    - extract_skills_from_languages(): Get skills from programming languages
    - extract_skills_from_frameworks(): Get skills from frameworks/libraries
    - extract_skills_from_files(): Get skills from file types (design, media, etc.)
"""

import os
from pathlib import Path
from typing import List, Set, Union
from collections import Counter


# Language to skills mapping
# NOTE: Language-specific programming skills are removed because languages are listed
# separately in the response. Skills here focus on concepts, paradigms, and specializations.
LANGUAGE_SKILLS = {
    # General Purpose Languages - Only paradigm/concept skills
    'Python': [],  # Programming skill removed, let frameworks add context
    'Java': ['Object-Oriented Programming'],
    'C#': ['Object-Oriented Programming'],
    'Go': [],
    'Rust': [],
    'PHP': [],
    'Ruby': [],
    'Kotlin': ['Object-Oriented Programming'],
    'Scala': ['Functional Programming'],
    'Elixir': ['Functional Programming'],
    'Erlang': ['Functional Programming'],
    
    # Frontend Languages - Skills from frameworks, not languages
    'JavaScript': [],
    'TypeScript': [],
    'HTML': [],
    'CSS': [],
    
    # Mobile Languages
    'Swift': ['iOS Development'],
    'Dart': [],  # Let Flutter framework add Mobile Development
    
    # Systems & Low-Level
    'C': [],
    'C++': ['Object-Oriented Programming'],
    'Assembly': [],
    
    # Data & Scientific
    'R': ['Statistical Analysis', 'Data Science'],
    'Julia': ['Scientific Computing'],
    'MATLAB': ['Scientific Computing'],
    
    # Scripting Languages - Automation is the skill
    'Shell': ['Automation'],
    'PowerShell': ['Automation'],
    'Batch': ['Automation'],
    'Perl': [],
    'Lua': [],
    'Groovy': [],
    
    # Functional Languages
    'Haskell': ['Functional Programming'],
    'F#': ['Functional Programming'],
    
    # Query Language
    'SQL': ['Database Querying'],
    
    # Markup/Data Formats
    'JSON': [],
    'XML': [],
    'YAML': [],
    
    # Notebooks
    'Jupyter Notebook': ['Data Analysis'],
}


# Framework to skills mapping with intelligent categorization
FRAMEWORK_SKILLS = {
    # Python Web Frameworks (names already in frameworks array, only add concept skills)
    'Django': ['RESTful APIs', 'ORM', 'MVC Architecture'],
    'Flask': ['RESTful APIs'],  # Removed: Microservices (can't determine architecture)
    'FastAPI': ['RESTful APIs', 'Async Programming', 'API Documentation'],
    
    # Python Data Science & ML (framework names in frameworks array)
    'TensorFlow': ['Machine Learning', 'Deep Learning', 'Neural Networks'],
    'PyTorch': ['Machine Learning', 'Deep Learning', 'Neural Networks'],
    'Keras': ['Machine Learning', 'Deep Learning', 'Neural Networks'],
    'Scikit-learn': ['Machine Learning', 'Statistical Modeling'],
    'Pandas': ['Data Analysis', 'Data Manipulation'],
    'NumPy': ['Numerical Computing', 'Scientific Computing'],
    'Streamlit': ['Data Visualization', 'Interactive Dashboards'],
    'Gradio': ['Machine Learning Interfaces', 'Interactive Demos'],
    
    # Python Tools
    'Celery': ['Task Queue Management', 'Asynchronous Processing'],
    'Scrapy': ['Web Scraping', 'Data Extraction'],
    'SQLAlchemy': ['ORM'],  # Removed: Database Management (redundant with ORM)
    'Pytest': ['Unit Testing', 'Test-Driven Development'],
    'Poetry': ['Dependency Management'],
    
    # JavaScript Frontend Frameworks (names in frameworks array)
    'React': ['Component-Based Architecture'],  # Removed: SPA (assumed), JSX (conditional)
    'Vue': ['Reactive UI'],  # Removed: PWA (assumed), SPA (assumed)
    'Angular': ['Dependency Injection', 'RxJS'],  # Removed: Enterprise Applications (too vague)
    'Svelte': ['Compiled Components', 'Reactive UI'],
    'Solid.js': ['Fine-Grained Reactivity'],  # Removed: Performance Optimization (assumed)
    'Preact': [],  # Lightweight alternative, no unique skills
    
    # Meta-Frameworks
    'Next.js': ['Server-Side Rendering', 'Static Site Generation'],
    'Nuxt.js': ['Server-Side Rendering'],
    'Gatsby': ['Static Site Generation', 'JAMstack', 'GraphQL'],
    'Remix': ['Nested Routing', 'Progressive Enhancement'],
    'Astro': ['Static Site Generation', 'Partial Hydration'],
    'SvelteKit': ['Server-Side Rendering'],
    
    # Backend JavaScript/Node.js
    'Express': ['RESTful APIs', 'Middleware'],
    'Koa': ['RESTful APIs', 'Async/Await'],
    'Fastify': ['High-Performance APIs', 'Schema Validation'],
    'Hapi': ['Enterprise APIs', 'Plugin Architecture'],
    'NestJS': ['Enterprise Architecture', 'Dependency Injection'],
    'Apollo Server': ['GraphQL Server', 'Schema Design'],
    
    # State Management
    'Redux': ['State Management', 'Predictable State Container'],
    'MobX': ['State Management', 'Observable State'],
    'Zustand': ['State Management'],
    'Recoil': ['State Management', 'Atomic State'],
    'Vuex': ['State Management'],
    'Pinia': ['State Management'],
    
    # UI Component Libraries (removed redundant "Component Libraries" and "Material Design")
    'Material-UI': [],  # Framework name in frameworks array
    'Ant Design': ['Enterprise UI'],
    'Chakra UI': ['Accessible Design', 'Design System'],
    'Semantic UI': ['Theming'],
    'Headless UI': ['Accessible Components'],
    'React Bootstrap': [],  # Just Bootstrap + React
    'Vuetify': [],  # Framework name in frameworks array
    'Mantine': [],  # Framework name in frameworks array
    
    # CSS Frameworks
    'Tailwind CSS': ['Utility-First CSS', 'Responsive Design'],
    'Bootstrap': ['Responsive Design', 'Grid System'],
    'Bulma': ['Responsive Design'],
    'Sass': ['CSS Preprocessing'],
    'Less': ['CSS Preprocessing'],
    'Emotion': ['CSS-in-JS'],
    'Styled Components': ['CSS-in-JS'],
    
    # Testing Frameworks
    'Jest': ['Unit Testing', 'Test-Driven Development'],
    'Vitest': ['Unit Testing'],
    'Mocha': ['Unit Testing', 'Test-Driven Development'],
    'Jasmine': ['Unit Testing', 'Behavior-Driven Development'],
    'Cypress': ['End-to-End Testing', 'Test Automation'],
    'Playwright': ['End-to-End Testing', 'Cross-Browser Testing'],
    'Testing Library': ['Component Testing', 'User-Centric Testing'],
    
    # Build Tools (removed redundant "Module Bundling")
    'Webpack': ['Build Optimization'],
    'Vite': [],  # Modern bundler, no unique skills
    'Rollup': [],  # Bundler, no unique skills
    'Parcel': [],  # Zero-config bundler, no unique skills
    'esbuild': [],  # Fast bundler, no unique skills
    'Turbopack': [],  # Next-gen bundler, no unique skills
    
    # GraphQL
    'GraphQL': ['GraphQL', 'API Design', 'Data Fetching'],
    'Apollo Client': ['GraphQL', 'State Management', 'Data Fetching'],
    'Relay': ['GraphQL', 'Data Management'],
    'URQL': ['GraphQL', 'Data Fetching'],
    
    # ORM & Database (removed redundant "Database Management" when ORM present)
    'Prisma': ['ORM'],
    'TypeORM': ['ORM'],
    'Sequelize': ['ORM'],
    'Mongoose': ['ODM', 'NoSQL'],
    'Drizzle ORM': ['ORM'],
    
    # Mobile Frameworks
    'React Native': ['Mobile Development', 'Cross-Platform Development'],
    'Expo': ['Mobile Development'],  # Removed: Rapid Prototyping (assumed)
    'Ionic': ['Hybrid Mobile Apps', 'Cross-Platform Development'],
    'NativeScript': ['Cross-Platform Development'],
    'Flutter': ['Mobile Development', 'Cross-Platform Development'],
    
    # Desktop Frameworks
    'Electron': ['Desktop Application Development', 'Cross-Platform Desktop'],
    'Tauri': ['Desktop Application Development'],
    
    # Java Frameworks
    'Spring Boot': ['Enterprise Java', 'Microservices', 'RESTful APIs'],
    'Spring': ['Enterprise Java', 'Dependency Injection'],
    'Hibernate': ['ORM', 'Java Persistence'],
    'JUnit': ['Unit Testing', 'Test-Driven Development'],
    'Mockito': ['Mocking', 'Unit Testing'],
    'Ktor': ['Asynchronous APIs'],
    
    # Ruby Frameworks
    'Rails': ['MVC Architecture', 'RESTful APIs', 'Convention over Configuration'],
    'Sinatra': ['Lightweight Web Apps'],
    'Hanami': [],  # Modern Ruby framework, no unique skills
    'RSpec': ['Behavior-Driven Development'],
    'Capybara': ['Integration Testing', 'Web Testing'],
    
    # PHP Frameworks
    'Laravel': ['MVC Architecture', 'Eloquent ORM'],
    'Symfony': ['Component-Based Architecture', 'Enterprise Development'],
    'CodeIgniter': [],  # Lightweight framework, no unique skills
    'CakePHP': ['Rapid Development'],
    'Yii': ['High-Performance Applications'],
    'Slim': [],  # Removed: Microservices (can't determine architecture)
    'PHPUnit': ['Unit Testing', 'Test-Driven Development'],
    
    # Go Frameworks
    'Gin': ['RESTful APIs', 'High-Performance Web'],
    'Echo': ['RESTful APIs'],
    'Fiber': ['High-Performance APIs'],
    'Beego': ['MVC Architecture'],  # Removed: Enterprise Applications (too vague)
    'Chi': ['RESTful APIs', 'HTTP Routing'],
    'Gorilla': ['HTTP Routing'],
    'GORM': ['ORM'],  # Removed: Database Management (redundant with ORM)
    
    # Rust Frameworks
    'Actix': ['High-Performance Web', 'Actor Model'],
    'Rocket': ['Type-Safe APIs'],
    'Axum': ['Async APIs'],
    'Warp': [],  # Functional web framework, no unique skills
    'Tokio': ['Async Programming', 'Concurrency'],
    'Serde': ['Serialization'],
    
    # .NET Frameworks
    'ASP.NET Core': ['Cross-Platform Web', 'Enterprise Development'],
    'Entity Framework': ['ORM'],  # Removed: Database Management (redundant with ORM)
    'Blazor': ['WebAssembly', 'Interactive Web'],
    'xUnit': ['Unit Testing', 'Test-Driven Development'],
    'NUnit': ['Unit Testing', 'Test-Driven Development'],
    
    # Other Libraries
    'Three.js': ['3D Graphics', 'WebGL', 'Interactive Visualization'],
    'D3.js': ['Data Visualization', 'Interactive Charts'],
    'Socket.IO': ['Real-Time Communication', 'WebSockets'],
    'Axios': [],  # HTTP client, removed "API Integration" (too generic)
    'Docker': ['Containerization'],  # Docker adds Containerization skill, not its own name
}


# File extension to skills mapping for CS-related file types
FILE_TYPE_SKILLS = {
    # UI/UX Design Files - CS-related design
    '.sketch': ['UI/UX Design', 'Interface Design', 'Prototyping'],
    '.fig': ['UI/UX Design', 'Collaborative Design', 'Prototyping'],
    
    # Web Graphics
    '.svg': ['Vector Graphics', 'Web Graphics'],
    '.webp': ['Web Graphics', 'Image Optimization'],
    
    # 3D & Game Development
    '.obj': ['3D Graphics', 'Game Development'],
    '.fbx': ['3D Graphics', 'Game Development'],
    
    # Documents & Technical Writing
    '.tex': ['LaTeX', 'Technical Writing', 'Document Preparation'],
    '.bib': ['Bibliography Management', 'Academic Writing', 'LaTeX'],
    '.md': ['Markdown', 'Documentation', 'Technical Writing'],
    '.rst': ['reStructuredText', 'Documentation', 'Python Documentation'],
    
    # Configuration & DevOps (framework names in frameworks array)
    '.dockerfile': ['Containerization'],
    '.dockerignore': ['Containerization'],
    'docker-compose.yml': ['Containerization', 'Multi-Container Applications'],
    '.gitlab-ci.yml': ['Continuous Integration', 'DevOps'],
    '.travis.yml': ['Continuous Integration', 'DevOps'],
    'jenkinsfile': ['CI/CD', 'Build Automation', 'DevOps'],  # lowercase for matching
    '.circleci/config.yml': ['Continuous Integration', 'DevOps'],
    
    # Database
    '.sql': ['SQL', 'Database Design', 'Query Optimization'],
    '.db': ['Database Management', 'SQLite'],
    '.sqlite': ['SQLite', 'Database Management'],
    
    # Jupyter & Data Science
    '.ipynb': ['Jupyter Notebooks', 'Data Analysis', 'Interactive Computing', 'Data Science'],
}


def extract_resume_skills(
    root_dir: Union[str, Path],
    languages: List[str] = None,
    frameworks: List[str] = None
) -> List[str]:
    """
    Extract comprehensive resume-ready skills from a project.
    
    Analyzes languages, frameworks, and file types to determine what professional
    skills are demonstrated in the project. This goes beyond simple detection to
    infer actual capabilities based on evidence.
    
    Args:
        root_dir: Path to the project directory
        languages: Optional pre-detected list of languages (will detect if not provided)
        frameworks: Optional pre-detected list of frameworks (will detect if not provided)
        
    Returns:
        Sorted list of unique skills, prioritized by relevance
        
    Example:
        >>> extract_resume_skills('/path/to/project')
        ['Backend Development', 'RESTful APIs', 'Containerization', 'Photo Editing']
    """
    from ..extractor.language_extractor import LanguageProjectAnalyzer as ProjectAnalyzer
    from ..extractor.framework_extractor import detect_frameworks_recursive
    
    print(f"🚀 Starting comprehensive skill extraction for: {root_dir}")
    root_path = Path(root_dir)
    all_skills = set()
    
    print(f"📂 Analyzing project directory: {root_path.resolve()}")
    
    # Get languages if not provided
    if languages is None:
        print(f"🔍 Languages not provided, detecting from project...")
        analyzer = ProjectAnalyzer()
        language_stats = analyzer.analyze_project_languages(str(root_path))
        # Extract language names (excluding 'Unknown' and empty stats)
        languages = [lang for lang, count in language_stats.items() 
                    if lang != 'Unknown' and count > 0]
        print(f"📝 Detected {len(languages)} languages: {', '.join(languages) if languages else 'None'}")
    else:
        print(f"📝 Using provided languages ({len(languages)}): {', '.join(languages)}")
    
    # Get frameworks if not provided
    if frameworks is None:
        print(f"🔧 Frameworks not provided, detecting from project...")
        # Use the default rules file path
        rules_path = Path(__file__).parent.parent / "config" / "frameworks_config.yml"
        if rules_path.exists():
            print(f"📋 Using framework rules from: {rules_path.name}")
            fw_results = detect_frameworks_recursive(root_path, str(rules_path))
            # Extract framework names from the nested structure
            frameworks = []
            for folder_frameworks in fw_results.get('frameworks', {}).values():
                for fw in folder_frameworks:
                    frameworks.append(fw.get('name', ''))
            print(f"⚙️  Detected {len(frameworks)} frameworks: {', '.join(frameworks) if frameworks else 'None'}")
        else:
            print(f"❌ Warning: Framework rules file not found at {rules_path}")
            frameworks = []
    else:
        print(f"⚙️  Using provided frameworks ({len(frameworks)}): {', '.join(frameworks)}")
    
    # Extract skills from each source
    print(f"\n🎯 Extracting skills from multiple sources...")
    
    lang_skills = extract_skills_from_languages(languages)
    print(f"📝 Language-based skills: {len(lang_skills)} found")
    all_skills.update(lang_skills)
    
    framework_skills = extract_skills_from_frameworks(frameworks)
    print(f"⚙️  Framework-based skills: {len(framework_skills)} found")
    all_skills.update(framework_skills)
    
    file_skills = extract_skills_from_files(root_path)
    print(f"📁 File-based skills: {len(file_skills)} found")
    all_skills.update(file_skills)
    
    # Cross-source inference: Add contextual skills based on language + framework combinations
    # This is where we infer skills like "Backend Development", "Frontend Development", etc.
    print(f"🧠 Inferring contextual skills from combinations...")
    contextual_skills = _infer_contextual_skills(languages, frameworks)
    print(f"💡 Contextual skills inferred: {len(contextual_skills)} found")
    all_skills.update(contextual_skills)
    
    # Sort and return
    final_skills = sorted(list(all_skills))
    print(f"\n✅ Skill extraction complete!")
    print(f"  📊 Total unique skills: {len(final_skills)}")
    if final_skills:
        print(f"  🎯 Top 5 skills: {', '.join(final_skills[:5])}")
        if len(final_skills) > 5:
            print(f"  ➕ And {len(final_skills) - 5} more...")
    print(f"")
    
    return final_skills


def _infer_contextual_skills(languages: List[str], frameworks: List[str]) -> Set[str]:
    """
    Infer contextual skills based on language + framework combinations.
    
    Relaxed detection: Recognizes both modern framework-based apps and traditional
    web applications (e.g., Java + HTML/CSS for JSP apps, Python + HTML for Django templates).
    
    Args:
        languages: List of detected languages
        frameworks: List of detected frameworks
        
    Returns:
        Set of inferred contextual skills
    """
    skills = set()
    lang_set = set(languages)
    framework_set = set(frameworks)
    
    # Backend Development - Relaxed: backend language is sufficient
    # Can be with or without frameworks (traditional or modern)
    backend_langs = {'Python', 'Java', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Kotlin', 'Scala', 'Elixir', 'Erlang'}
    backend_frameworks = {'Django', 'Flask', 'FastAPI', 'Express', 'Koa', 'Fastify', 'Hapi', 
                         'NestJS', 'Spring Boot', 'Spring', 'Rails', 'Sinatra', 'Laravel', 
                         'Symfony', 'Gin', 'Echo', 'Fiber', 'Actix', 'Rocket', 'ASP.NET Core'}
    
    # Frontend Development - Relaxed: 
    # - Modern: JS/TS with frameworks (React, Vue, etc.)
    # - Traditional: HTML + CSS (static sites or server-rendered)
    frontend_langs = {'JavaScript', 'TypeScript'}
    frontend_frameworks = {'React', 'Vue', 'Angular', 'Svelte', 'Solid.js', 'Preact',
                          'Next.js', 'Nuxt.js', 'Gatsby', 'Remix', 'Astro', 'SvelteKit'}
    
    # Detect backend presence (language-based, more relaxed)
    has_backend = bool(lang_set & backend_langs)
    
    # Detect frontend presence (modern frameworks OR traditional HTML+CSS)
    has_modern_frontend = (lang_set & frontend_langs) and (framework_set & frontend_frameworks)
    has_traditional_frontend = ('HTML' in lang_set) or ('CSS' in lang_set)
    has_frontend = has_modern_frontend or has_traditional_frontend
    
    # Full-Stack Development - Relaxed: backend language + any frontend indication
    # This covers:
    # - Modern: Python + Django + React
    # - Traditional: Java + HTML/CSS (JSP), PHP + HTML/CSS, Python + Django templates
    if has_backend and has_frontend:
        skills.add('Full-Stack Development')
    else:
        # Only add Frontend or Backend if it's NOT a full-stack project
        if has_backend:
            skills.add('Backend Development')
        if has_modern_frontend:
            skills.add('Frontend Development')
        elif has_traditional_frontend and not has_backend:
            # Pure frontend (HTML/CSS only, no backend language)
            skills.add('Frontend Development')
    
    # Mobile Development - if mobile language + mobile framework
    mobile_frameworks = {'React Native', 'Expo', 'Ionic', 'NativeScript', 'Flutter'}
    
    if 'Swift' in lang_set:
        skills.add('Mobile Development')  # Swift is specifically for iOS
    
    if 'Dart' in lang_set and 'Flutter' in framework_set:
        skills.add('Mobile Development')
    
    if (lang_set & frontend_langs) and (framework_set & mobile_frameworks):
        skills.add('Mobile Development')
    
    # Data Science - if data science language + data frameworks
    if 'Python' in lang_set:
        data_frameworks = {'Pandas', 'NumPy', 'Scikit-learn', 'Jupyter Notebook'}
        if framework_set & data_frameworks:
            skills.add('Data Science')
    
    if 'R' in lang_set:
        skills.add('Data Science')  # R is specifically for data science
    
    # Machine Learning - if ML frameworks are present
    ml_frameworks = {'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn'}
    if framework_set & ml_frameworks:
        skills.add('Machine Learning')
    
    # DevOps - only if there's evidence of automation + infrastructure
    # Require BOTH containerization AND scripting to infer DevOps
    has_containers = 'Docker' in framework_set
    has_scripting = lang_set & {'Shell', 'PowerShell', 'Batch'}
    
    if has_containers and has_scripting:
        skills.add('DevOps')
    
    # Note: CI/CD tools (Jenkins, GitLab CI, etc.) will add DevOps via file detection
    
    return skills


def extract_skills_from_languages(languages: List[str]) -> Set[str]:
    """
    Extract skills from detected programming languages.
    
    Only includes skills that are directly demonstrated by the language itself.
    More complex skills (like "Full-Stack Development") are inferred from
    language + framework combinations in the main extract_skills function.
    
    Args:
        languages: List of detected programming languages
        
    Returns:
        Set of skills derived from the languages
    """
    print(f"  📝 Processing {len(languages)} languages for skill extraction...")
    skills = set()
    skills_added = 0
    
    for language in languages:
        if language in LANGUAGE_SKILLS:
            lang_skills = LANGUAGE_SKILLS[language]
            if lang_skills:
                print(f"    ✓ {language}: {', '.join(lang_skills)}")
                skills_added += len(lang_skills)
            skills.update(lang_skills)
        else:
            print(f"    ⚠️  {language}: No skill mapping found")
    
    # Web Design skill when HTML + CSS are detected together
    if 'HTML' in languages and 'CSS' in languages:
        print(f"    💡 Combination detected: HTML + CSS → Web Design")
        skills.add('Web Design')
        skills_added += 1
    
    print(f"  📊 Language skills extracted: {skills_added} skills from {len(languages)} languages")
    return skills


def extract_skills_from_frameworks(frameworks: List[str]) -> Set[str]:
    """
    Extract skills from detected frameworks and libraries.
    
    Only includes skills that are directly demonstrated by the framework itself.
    Broader contextual skills (like "Backend Development", "Full-Stack Development")
    are inferred in _infer_contextual_skills based on language + framework combinations.
    
    Args:
        frameworks: List of detected frameworks
        
    Returns:
        Set of skills derived from the frameworks
    """
    print(f"  ⚙️  Processing {len(frameworks)} frameworks for skill extraction...")
    skills = set()
    skills_added = 0
    
    # Add skills directly from framework mappings
    for framework in frameworks:
        if framework in FRAMEWORK_SKILLS:
            fw_skills = FRAMEWORK_SKILLS[framework]
            if fw_skills:
                print(f"    ✓ {framework}: {', '.join(fw_skills)}")
                skills_added += len(fw_skills)
            skills.update(fw_skills)
        else:
            print(f"    ⚠️  {framework}: No skill mapping found")
    
    # Add framework combination-based specializations
    # These are skills that only emerge from using MULTIPLE frameworks together
    framework_set = set(frameworks)
    
    print(f"    🔍 Checking for framework combination specializations...")
    
    # Machine Learning Engineering - using multiple ML frameworks shows ML engineering skill
    ml_frameworks = {'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn'}
    ml_detected = framework_set & ml_frameworks
    if len(ml_detected) >= 2:
        print(f"    💡 ML Engineering: {', '.join(ml_detected)} → Machine Learning Engineering")
        skills.add('Machine Learning Engineering')
        skills_added += 1
    
    # Testing Expertise - using multiple testing frameworks shows testing specialization
    test_frameworks = {'Jest', 'Pytest', 'Cypress', 'Playwright', 'JUnit', 'Vitest', 'Mocha', 'RSpec'}
    test_detected = framework_set & test_frameworks
    if len(test_detected) >= 2:
        print(f"    💡 Test Specialization: {', '.join(test_detected)} → Test Automation")
        skills.add('Test Automation')
        skills_added += 1
    
    print(f"  📊 Framework skills extracted: {skills_added} skills from {len(frameworks)} frameworks")
    return skills


def extract_skills_from_files(root_dir: Union[str, Path]) -> Set[str]:
    """
    Extract skills from file types, especially for creative and specialized work.
    
    This is particularly useful for detecting skills like photography, graphic design,
    video editing, and other non-coding skills demonstrated in a project.
    
    Args:
        root_dir: Path to the project directory
        
    Returns:
        Set of skills derived from file types
    """
    print(f"  📁 Scanning files in directory for specialized skills...")
    root_path = Path(root_dir)
    skills = set()
    file_counter = Counter()
    files_scanned = 0
    skills_from_files = 0
    
    # Walk through directory and count file types
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip common ignored directories
        skip_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'build', 'dist'}
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        for filename in filenames:
            files_scanned += 1
            ext = os.path.splitext(filename)[1].lower()
            
            # Also check for special filenames without extensions
            if filename.lower() in FILE_TYPE_SKILLS:
                file_skills = FILE_TYPE_SKILLS[filename.lower()]
                print(f"    🎯 Special file '{filename}' → {', '.join(file_skills)}")
                skills.update(file_skills)
                skills_from_files += len(file_skills)
            
            if ext in FILE_TYPE_SKILLS:
                file_counter[ext] += 1
    
    print(f"    📊 Scanned {files_scanned} files, found {len(file_counter)} relevant file types")
    
    # Add skills based on file type counts with thresholds
    print(f"    🔍 Analyzing file type patterns with thresholds...")
    
    # UI/UX Design skills
    design_files = [('.sketch', 'Sketch'), ('.fig', 'Figma')]
    for ext, name in design_files:
        if file_counter.get(ext, 0) >= 1:
            design_skills = FILE_TYPE_SKILLS[ext]
            print(f"    🎨 {name} files ({file_counter[ext]}) → {', '.join(design_skills)}")
            skills.update(design_skills)
            skills_from_files += len(design_skills)
    
    # 3D graphics and game development
    graphics_exts = {'.obj', '.fbx'}
    graphics_files = [ext for ext in graphics_exts if file_counter.get(ext, 0) >= 1]
    if graphics_files:
        print(f"    🎯 3D/Game files ({', '.join(graphics_files)}) → 3D Graphics")
        skills.add('3D Graphics')
        skills_from_files += 1
    
    # Technical writing
    if file_counter.get('.tex', 0) >= 1:
        tex_skills = FILE_TYPE_SKILLS['.tex']
        print(f"    📄 LaTeX files ({file_counter['.tex']}) → {', '.join(tex_skills)}")
        skills.update(tex_skills)
        skills_from_files += len(tex_skills)
    
    if file_counter.get('.md', 0) >= 5:
        print(f"    📖 Markdown files ({file_counter['.md']}) → Documentation + Technical Writing")
        skills.add('Documentation')
        skills.add('Technical Writing')
        skills_from_files += 2
    
    # Data Science indicators
    if file_counter.get('.ipynb', 0) >= 1:
        jupyter_skills = FILE_TYPE_SKILLS['.ipynb']
        print(f"    🔬 Jupyter notebooks ({file_counter['.ipynb']}) → {', '.join(jupyter_skills)}")
        skills.update(jupyter_skills)
        skills_from_files += len(jupyter_skills)
    
    print(f"  📊 File skills extracted: {skills_from_files} skills from {len(file_counter)} file types")
    return skills


def extract_languages_from_project(root_dir: Union[str, Path]) -> List[str]:
    """
    Extract programming languages from a project directory.
    
    Args:
        root_dir: Path to the project directory
        
    Returns:
        List of detected programming languages
    """
    from ..extractor.language_extractor import LanguageProjectAnalyzer as ProjectAnalyzer
    
    analyzer = ProjectAnalyzer()
    language_stats = analyzer.analyze_project_languages(str(root_dir))
    # Return languages with files > 0, excluding 'Unknown'
    return [lang for lang, count in language_stats.items() 
            if lang != 'Unknown' and count > 0]


def extract_frameworks_from_project(root_dir: Union[str, Path]) -> List[str]:
    """
    Extract frameworks from a project directory, returning a deduplicated list.
    Uses confidence scores from detector when available and picks the highest.
    """
    from ..extractor.framework_extractor import detect_frameworks_recursive

    root_path = Path(root_dir)
    rules_path = Path(__file__).parent.parent / "config" / "frameworks_config.yml"

    if not rules_path.exists():
        print(f"Warning: Framework rules file not found at {rules_path}")
        return []

    fw_results = detect_frameworks_recursive(root_path, str(rules_path))

    # collect best confidence per framework name
    best: dict = {}
    for folder_frameworks in fw_results.get("frameworks", {}).values():
        for fw in folder_frameworks:
            name = (fw.get("name") or "").strip()
            if not name:
                continue
            conf = fw.get("confidence", 1.0)
            # normalize name (trim + consistent casing)
            key = name.strip()
            # keep max confidence
            prev = best.get(key)
            if prev is None or conf > prev:
                best[key] = conf

    # return frameworks sorted by confidence desc, then name
    sorted_fw = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
    return [name for name, _ in sorted_fw]

def analyze_project_skills(root_dir: Union[str, Path]) -> dict:
    """
    Comprehensive project skill analysis that integrates with existing analysis modules.
    
    Returns a structured analysis including languages, frameworks, and inferred skills
    suitable for integration with the main project analysis pipeline.
    
    Args:
        root_dir: Path to the project directory
        
    Returns:
        Dictionary containing languages, frameworks, skills, and skill categories
    """
    print(f"🎯 Starting comprehensive project skill analysis")
    print(f"📂 Target directory: {root_dir}")
    print(f"=" * 60)
    
    root_path = Path(root_dir)
    
    # Extract languages and frameworks
    print(f"🔍 Phase 1: Language and Framework Detection")
    languages = extract_languages_from_project(root_path)
    frameworks = extract_frameworks_from_project(root_path)
    
    # Extract all skills
    print(f"\n🎯 Phase 2: Comprehensive Skill Extraction")
    skills = extract_resume_skills(root_path, languages, frameworks)
    
    # Categorize skills
    print(f"\n📋 Phase 3: Skill Categorization")
    categories = get_skill_categories()
    categorized_skills = {}
    uncategorized_count = 0
    
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
            if 'Other' not in categorized_skills:
                categorized_skills['Other'] = []
            categorized_skills['Other'].append(skill)
            uncategorized_count += 1
    
    # Print categorization summary
    print(f"  📊 Skills categorized into {len(categorized_skills)} categories:")
    for category, cat_skills in categorized_skills.items():
        print(f"    • {category}: {len(cat_skills)} skills")
    
    result = {
        'languages': languages,
        'frameworks': frameworks,
        'skills': skills,
        'skill_categories': categorized_skills,
        'total_skills': len(skills),
        'project_path': str(root_path.resolve())
    }
    
    print(f"\n" + "=" * 60)
    print(f"✅ Project skill analysis complete!")
    print(f"  📝 Languages: {len(languages)}")
    print(f"  ⚙️  Frameworks: {len(frameworks)}")
    print(f"  🎯 Total Skills: {len(skills)}")
    print(f"  📋 Categories: {len(categorized_skills)}")
    print(f"")
    
    return result


def get_skill_categories() -> dict:
    """
    Return a categorized view of all possible CS-related skills.
    
    Returns:
        Dictionary mapping skill categories to lists of skills
    """
    categories = {
        'Programming Paradigms': set(),
        'Web Development': set(),
        'Mobile Development': set(),
        'Data Science & ML': set(),
        'UI/UX Design': set(),
        'DevOps & Infrastructure': set(),
        'Testing & QA': set(),
        'Database & ORM': set(),
        'Game Development': set(),
        'Other': set(),
    }
    
    # Categorize language skills
    for skills in LANGUAGE_SKILLS.values():
        for skill in skills:
            if any(keyword in skill for keyword in ['Programming', 'Development', 'Scripting']):
                categories['Programming Paradigms'].add(skill)
    
    # Categorize framework skills
    for skills in FRAMEWORK_SKILLS.values():
        for skill in skills:
            if any(keyword in skill for keyword in ['Machine Learning', 'Data Science', 'AI', 'Deep Learning']):
                categories['Data Science & ML'].add(skill)
            elif any(keyword in skill for keyword in ['Mobile', 'iOS', 'Android']):
                categories['Mobile Development'].add(skill)
            elif any(keyword in skill for keyword in ['Testing', 'Test-Driven', 'QA', 'Quality']):
                categories['Testing & QA'].add(skill)
            elif any(keyword in skill for keyword in ['DevOps', 'Docker', 'CI/CD', 'Container']):
                categories['DevOps & Infrastructure'].add(skill)
            elif any(keyword in skill for keyword in ['ORM', 'Database', 'SQL']):
                categories['Database & ORM'].add(skill)
            elif any(keyword in skill for keyword in ['Frontend', 'Backend', 'Web', 'API']):
                categories['Web Development'].add(skill)
    
    # Categorize file type skills
    for skills in FILE_TYPE_SKILLS.values():
        for skill in skills:
            if any(keyword in skill for keyword in ['UI/UX', 'Interface', 'Prototyping']):
                categories['UI/UX Design'].add(skill)
            elif any(keyword in skill for keyword in ['3D', 'Graphics', 'Game']):
                categories['Game Development'].add(skill)
    
    return {k: sorted(list(v)) for k, v in categories.items() if v}

