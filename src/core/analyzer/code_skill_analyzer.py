import re
import os
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from tqdm import tqdm

# Import optimized file walking and centralized configuration
from ..extractor.language_extractor import FileWalker
from ..config.skill_mappings import get_language_config
from .file_analyzer import FileAnalyzer

class CodeSkillAnalyzer:
    """Modern code skill analyzer with optimized file walking and centralized configuration."""
    
    def __init__(self):
        """Initialize analyzer with centralized configuration and optimized file walking."""
        # Load centralized configuration
        self.config = get_language_config()
        
        # Derive supported languages from available skill mapping files
        self.supported_languages = self._discover_supported_languages()
        
        # Initialize language detector and file analyzer components
        from ..extractor.language_parser import LanguageDetector
        self.language_detector = LanguageDetector()
        self.file_walker = FileWalker(self.language_detector)
        self.file_analyzer = FileAnalyzer(self.language_detector)
        
        # Get data directory from centralized config
        self._data_dir = self._get_data_directory()
        
        # Cache for compiled regex patterns and loaded mappings
        self._compiled_patterns = {}
        self._skill_mappings = {}
        
        print(f"🎯 CodeSkillAnalyzer initialized with {len(self.supported_languages)} supported languages")
    
    def _get_data_directory(self) -> Path:
        """Get data directory using consistent path resolution."""
        # Go up from src/core/analyzer to src/data
        return Path(__file__).resolve().parents[2] / "data"
    
    def _discover_supported_languages(self) -> Set[str]:
        """Discover supported languages from available skill mapping files."""
        languages = set()
        data_dir = self._get_data_directory()
        
        # Find all skill_mapping_*.json files
        for mapping_file in data_dir.glob("skill_mapping_*.json"):
            # Extract language name from filename
            lang_name = mapping_file.stem.replace("skill_mapping_", "")
            languages.add(lang_name.lower())
        
        return languages
    
    def _get_skill_mapping_path(self, language: str) -> Optional[Path]:
        """Get skill mapping path for a language using centralized configuration."""
        lang = language.lower()
        mapping_path = self._data_dir / f"skill_mapping_{lang}.json"
        return mapping_path if mapping_path.exists() else None


    def _load_skill_mapping(self, language: str) -> Optional[Dict[str, List[str]]]:
        """Load and cache skill mapping for a language with error handling."""
        if language in self._skill_mappings:
            return self._skill_mappings[language]
        
        mapping_path = self._get_skill_mapping_path(language)
        if not mapping_path:
            print(f"⚠️ No skill mapping found for language: {language}")
            return None
        
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert to skill -> identifiers mapping
            mapping = {entry["skill"]: entry["identifiers"] for entry in data}
            self._skill_mappings[language] = mapping
            
            # Pre-compile regex patterns for performance
            self._compile_patterns(language, mapping)
            
            return mapping
        
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"❌ Error loading skill mapping for {language}: {e}")
            return None
    
    def _compile_patterns(self, language: str, mapping: Dict[str, List[str]]):
        """Pre-compile regex patterns for better performance."""
        if language not in self._compiled_patterns:
            self._compiled_patterns[language] = {}
        
        for skill, patterns in mapping.items():
            compiled = []
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern, re.MULTILINE))
                except re.error as e:
                    print(f"⚠️ Invalid regex pattern for {skill} in {language}: {pattern} - {e}")
            
            self._compiled_patterns[language][skill] = compiled


    def analyze_code_file(self, file_path: str, language: str, loc: int) -> Dict[str, Any]:
        """Analyze a single file for skills using pre-compiled patterns."""
        # Load skill mapping for language
        mapping = self._load_skill_mapping(language)
        if not mapping:
            return {"error": f"No mapping for language: {language}"}
        
        # Validate file exists
        if not os.path.exists(file_path):
            return {"error": f"File missing: {file_path}"}
        
        # Read file content with error handling
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            return {"error": f"Error reading file {file_path}: {e}"}
        
        # Analyze using pre-compiled patterns
        scores = defaultdict(lambda: {"raw_count": 0, "identifier_list": []})
        compiled_patterns = self._compiled_patterns.get(language, {})
        
        for skill, patterns in compiled_patterns.items():
            total = 0
            identifier_matches = []
            
            for compiled_pattern in patterns:
                try:
                    matches = compiled_pattern.findall(text)
                    if matches:
                        identifier_matches.append(f"{compiled_pattern.pattern} ({len(matches)})")
                    total += len(matches)
                except Exception as e:
                    continue  # Skip problematic patterns
            
            if total > 0:
                scores[skill]["raw_count"] = total
                scores[skill]["identifier_list"] = identifier_matches
                scores[skill]["density_score"] = round((total / max(loc, 1)) * 100, 4)
        
        # Only return skills with matches
        non_zero_skills = {s: info for s, info in scores.items() if info["raw_count"] > 0}
        
        return {
            "file_path": file_path,
            "language": language,
            "loc": loc,
            "mapping_used": str(self._get_skill_mapping_path(language)),
            "skill_scores": non_zero_skills
        }


    def analyze_project_skills(self, project_path: str) -> Dict[str, Any]:
        """Analyze project skills using optimized file walking and progress reporting."""
        print(f"🚀 Starting skill analysis for project: {project_path}")
        print(f"🔍 Using optimized file walk with centralized filtering")
        
        # Initialize summary statistics
        summary = {
            "total_files": 0,
            "files_analyzed": 0,
            "files_skipped": 0,
            "languages_encountered": set(),
            "unsupported_languages": defaultdict(int),
            "global_skill_counts": defaultdict(int),
            "skills_by_language": defaultdict(lambda: defaultdict(int))
        }
        
        reports = []
        
        # Use optimized file walking with progress reporting
        with tqdm(desc="🎯 Analyzing skills", unit=" files") as pbar:
            for file_path in self.file_walker.walk_source_files(project_path, filter_files=True):
                pbar.update(1)
                summary["total_files"] += 1
                
                # Get language and file stats using existing analyzer
                try:
                    language, file_stats = self.file_analyzer.analyze_single_file(file_path)
                    
                    if not language or language.lower() not in self.supported_languages:
                        if language:
                            summary["unsupported_languages"][language.lower()] += 1
                        summary["files_skipped"] += 1
                        continue
                    
                    # Get lines of code from file stats
                    loc = file_stats.code_lines if file_stats else 0
                    language = language.lower()
                    
                    # Analyze file for skills
                    result = self.analyze_code_file(file_path, language, loc)
                    
                    if "error" in result:
                        summary["files_skipped"] += 1
                        continue
                    
                    # Aggregate skill counts
                    summary["languages_encountered"].add(language)
                    for skill, info in result["skill_scores"].items():
                        count = info["raw_count"]
                        summary["global_skill_counts"][skill] += count
                        summary["skills_by_language"][language][skill] += count
                    
                    reports.append(result)
                    summary["files_analyzed"] += 1
                    
                    # Update progress description
                    if summary["files_analyzed"] % 10 == 0:
                        pbar.set_description(f"🎯 Analyzed {summary['files_analyzed']} files, {len(summary['global_skill_counts'])} skills found")
                
                except Exception as e:
                    print(f"⚠️ Error analyzing {file_path}: {e}")
                    summary["files_skipped"] += 1
                    continue
        
        # Process final results
        summary["languages_encountered"] = list(summary["languages_encountered"])
        summary["unsupported_languages"] = dict(summary["unsupported_languages"])
        
        # Sort results by skill frequency
        summary["global_skill_counts"] = dict(
            sorted(summary["global_skill_counts"].items(), key=lambda x: x[1], reverse=True)
        )
        
        # Sort skills within each language
        sorted_lang_skills = {}
        for lang, skill_dict in summary["skills_by_language"].items():
            sorted_lang_skills[lang] = dict(
                sorted(skill_dict.items(), key=lambda x: x[1], reverse=True)
            )
        summary["skills_by_language"] = sorted_lang_skills
        
        print(f"✅ Skill analysis complete:")
        print(f"  📊 {summary['files_analyzed']} files analyzed")
        print(f"  🎯 {len(summary['global_skill_counts'])} unique skills found")
        print(f"  🌐 {len(summary['languages_encountered'])} languages processed")
        
        return {
            "summary": summary,
            "file_reports": reports
        }


# Legacy function wrapper for backward compatibility
def run_skill_extraction(metadata_path: str, output_path: str) -> Dict[str, Any]:
    """Legacy wrapper - use CodeSkillAnalyzer.analyze_project_skills() for new code."""
    print("⚠️ Using legacy run_skill_extraction - consider using CodeSkillAnalyzer class")
    
    if not os.path.exists(metadata_path):
        return {"error": f"Metadata not found: {metadata_path}"}
    
    # Extract project root from metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    project_root = meta["project_root"]
    
    # Use modern analyzer
    analyzer = CodeSkillAnalyzer()
    return analyzer.analyze_project_skills(project_root)