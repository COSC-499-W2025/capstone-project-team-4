import os
from pathlib import Path
from typing import Dict, Iterator
from .language_parser import Constants, LanguageConfig, LanguageDetector
from ..analyzer.file_analyzer import FileStats, FileAnalyzer


class FileWalker:
    """Handles project file traversal with filtering using centralized configuration."""
    
    def __init__(self, language_detector: LanguageDetector):
        self.language_detector = language_detector
        # Get skip patterns from centralized configuration
        skip_patterns = self.language_detector.config._config.get('skip_patterns', {})
        self.skip_directories = set(skip_patterns.get('skip_directories', []))
        print(f"📋 FileWalker initialized with {len(self.skip_directories)} directory skip patterns")
    
    def walk_source_files(self, project_path: str, filter_files: bool = True) -> Iterator[str]:
        """Walk through project files, yielding paths of relevant files with centralized filtering.
        
        Args:
            project_path: Path to scan
            filter_files: If True, apply file filtering during walk (default). If False, yield all files.
        """
        print(f"🔍 Starting optimized file walk from: {project_path}")
        print(f"🎯 Filter mode: {'Enabled - skipping unwanted files during walk' if filter_files else 'Disabled - yielding all files'}")
        
        total_dirs = 0
        total_files_found = 0
        total_files_yielded = 0
        total_dirs_filtered = 0
        total_files_filtered = 0
        
        for root, dirs, files in os.walk(project_path):
            # Filter out unwanted directories using centralized configuration
            original_dir_count = len(dirs)
            dirs[:] = [d for d in dirs if d not in self.skip_directories]
            filtered_dirs = original_dir_count - len(dirs)
            total_dirs_filtered += filtered_dirs
            
            total_dirs += 1
            dir_name = os.path.basename(root) or "root"
            
            # Count and filter files
            files_in_dir = len(files)
            total_files_found += files_in_dir
            files_yielded_in_dir = 0
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Apply file filtering during walk if enabled
                if filter_files:
                    if self.should_analyze_file(file_path):
                        total_files_yielded += 1
                        files_yielded_in_dir += 1
                        if total_files_yielded % 50 == 0:  # Progress update every 50 files
                            print(f"    📄 Yielded {total_files_yielded} files...")
                        yield file_path
                    else:
                        total_files_filtered += 1
                else:
                    # No filtering - yield all files
                    total_files_yielded += 1
                    files_yielded_in_dir += 1
                    if total_files_yielded % 50 == 0:
                        print(f"    📄 Processed {total_files_yielded} files...")
                    yield file_path
            
            # Progress report for this directory
            files_filtered_in_dir = files_in_dir - files_yielded_in_dir
            if filter_files and (files_yielded_in_dir > 0 or files_filtered_in_dir > 0):
                print(f"  📁 {dir_name}: {files_yielded_in_dir} files yielded, {files_filtered_in_dir} files filtered, {filtered_dirs} dirs filtered")
            elif not filter_files and files_yielded_in_dir > 0:
                print(f"  📁 {dir_name}: {files_yielded_in_dir} files found, {filtered_dirs} dirs filtered")
        
        print(f"✅ Optimized file walk complete:")
        print(f"  📊 {total_dirs} directories scanned, {total_dirs_filtered} directories filtered")
        print(f"  📊 {total_files_found} files found, {total_files_yielded} files yielded")
        if filter_files:
            print(f"  🎯 {total_files_filtered} files filtered during walk (efficiency gain!)")
    
    def should_analyze_file(self, file_path: str) -> bool:
        """Determine if a file should be analyzed using centralized configuration rules."""
        return self.language_detector.should_analyze_file(file_path)


class LanguageProjectAnalyzer:
    """High-level project language analysis combining all components."""
    
    def __init__(self):
        self.config = LanguageConfig()
        self.language_detector = LanguageDetector(self.config)
        self.file_walker = FileWalker(self.language_detector)
        self.file_analyzer = FileAnalyzer(self.language_detector)
    
    def analyze_project_languages(self, project_path: str, include_filtered: bool = False) -> Dict[str, int]:
        """Analyze programming languages in a project directory (file counts only)."""
        language_stats = {}
        analyzed_count = 0
        
        print(f"🔎 Starting efficient language analysis for: {project_path}")
        print(f"💡 Using optimized file walk - unwanted files already filtered out!")
        
        # Use filtered file walk - only get files we actually want to analyze
        for file_path in self.file_walker.walk_source_files(project_path, filter_files=True):
            analyzed_count += 1
            language = self.file_analyzer.detect_language_by_extension(file_path)
            language_stats[language] = language_stats.get(language, 0) + 1
            
            if analyzed_count % 20 == 0:
                print(f"    📊 Analyzed {analyzed_count} files, found {len(language_stats)} languages")
        
        # Handle filtered count reporting if requested
        if include_filtered:
            # Need to walk again without filtering to get filtered count
            print(f"📊 Calculating filtered file count for reporting...")
            total_files = sum(1 for _ in self.file_walker.walk_source_files(project_path, filter_files=False))
            filtered_count = total_files - analyzed_count
            if filtered_count > 0:
                language_stats['Filtered'] = filtered_count
                print(f"📋 Found {filtered_count} filtered files")
        
        print(f"✅ Efficient language analysis complete: {analyzed_count} files analyzed")
        return language_stats
    
    def analyze_project_lines_of_code(self, project_path: str, include_filtered: bool = False) -> Dict[str, FileStats]:
        """Analyze lines of code by language in a project directory."""
        language_stats = {}
        analyzed_count = 0
        total_lines = 0
        
        print(f"📏 Starting efficient lines of code analysis for: {project_path}")
        print(f"💡 Using optimized file walk - unwanted files already filtered out!")
        
        # Use filtered file walk - only get files we actually want to analyze
        for file_path in self.file_walker.walk_source_files(project_path, filter_files=True):
            analyzed_count += 1
            file_name = os.path.basename(file_path)
            print(f"    📄 Analyzing: {file_name} ({analyzed_count} files processed)")
            
            language, stats = self.file_analyzer.analyze_single_file(file_path)
            
            if language not in language_stats:
                language_stats[language] = FileStats()
                print(f"    🆕 New language detected: {language}")
            
            language_stats[language].add(stats)
            total_lines += stats.total_lines
            
            if analyzed_count % 15 == 0:
                print(f"    📊 Progress: {analyzed_count} files, {total_lines} total lines, {len(language_stats)} languages")
        
        # Handle filtered reporting if requested
        if include_filtered:
            print(f"📊 Calculating filtered file statistics...")
            total_files = sum(1 for _ in self.file_walker.walk_source_files(project_path, filter_files=False))
            filtered_count = total_files - analyzed_count
            if filtered_count > 0:
                language_stats['Filtered'] = FileStats()
                language_stats['Filtered'].files = filtered_count
                print(f"📋 Added {filtered_count} filtered files to stats")
        
        print(f"✅ Efficient LOC analysis complete: {analyzed_count} files, {total_lines} total lines analyzed")
        return language_stats
    
    def get_unknown_files(self, project_path: str, limit: int = 20) -> list:
        """Get list of files classified as 'Unknown' using efficient file walk."""
        unknown_files = []
        
        # Use filtered file walk - only get files we actually want to analyze
        for file_path in self.file_walker.walk_source_files(project_path, filter_files=True):
            if self.file_analyzer.detect_language_by_extension(file_path) == 'Unknown':
                unknown_files.append(file_path)
                if len(unknown_files) >= limit:
                    break
        
        return unknown_files


class StatsFormatter:
    """Formats and displays analysis results."""
    
    @staticmethod
    def format_analysis_to_json(analyzer: LanguageProjectAnalyzer, project_path: str, include_filtered: bool = False) -> dict:
        """Format analysis results as JSON data structure."""
        file_stats = analyzer.analyze_project_languages(project_path, include_filtered=include_filtered)
        loc_stats = analyzer.analyze_project_lines_of_code(project_path, include_filtered=include_filtered)
        
        # Convert FileStats objects to dictionaries for JSON serialization
        json_data = {
            "project_path": str(project_path),
            "file_counts": file_stats,
            "lines_of_code": {
                lang: {
                    "files": stats.files,
                    "total_lines": stats.total_lines,
                    "code_lines": stats.code_lines,
                    "comment_lines": stats.comment_lines,
                    "blank_lines": stats.blank_lines
                } for lang, stats in loc_stats.items()
            }
        }
        
        return json_data
    
    @staticmethod
    def save_analysis_to_json(analyzer: LanguageProjectAnalyzer, project_path: str, output_file: str = None, include_filtered: bool = False) -> str:
        """Save analysis results to JSON file and return the file path."""
        import json
        from pathlib import Path
        
        json_data = StatsFormatter.format_analysis_to_json(analyzer, project_path, include_filtered)
        
        # Generate default filename if not provided
        if output_file is None:
            project_name = Path(project_path).name
            output_file = f"{project_name}_language_analysis.json"
        
        # Ensure the output directory exists
        output_path = Path(output_file)
        if not output_path.is_absolute():
            # Save to outputs directory by default
            outputs_dir = Path.cwd() / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            output_path = outputs_dir / output_file
        
        # Write JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        
        return str(output_path)
    
    @staticmethod
    def print_detailed_language_stats(analyzer: LanguageProjectAnalyzer, project_path: str, show_filtered: bool = False):
        """Print comprehensive language statistics including lines of code."""
        print(f"📊 Language Analysis for: {project_path}")
        print("=" * 60)
        
        # Get both file counts and lines of code
        file_stats = analyzer.analyze_project_languages(project_path, include_filtered=show_filtered)
        loc_stats = analyzer.analyze_project_lines_of_code(project_path, include_filtered=show_filtered)
        
        # Combine and sort by lines of code
        combined_stats = []
        for lang in set(list(file_stats.keys()) + list(loc_stats.keys())):
            if lang == 'Filtered' and not show_filtered:
                continue
                
            file_count = file_stats.get(lang, 0)
            loc_data = loc_stats.get(lang, FileStats())
            
            combined_stats.append({
                'language': lang,
                'files': file_count,
                'total_lines': loc_data.total_lines,
                'code_lines': loc_data.code_lines,
                'comment_lines': loc_data.comment_lines,
                'blank_lines': loc_data.blank_lines
            })
        
        # Sort by code lines (descending)
        combined_stats.sort(key=lambda x: x['code_lines'], reverse=True)
        
        # Print header
        print(f"{'Language':<12} {'Files':<6} {'Total':<8} {'Code':<8} {'Comments':<9} {'Blank':<6}")
        print("-" * 60)
        
        total_files = 0
        total_code = 0
        total_lines = 0
        
        for stat in combined_stats:
            lang = stat['language']
            files = stat['files']
            total = stat['total_lines']
            code = stat['code_lines']
            comments = stat['comment_lines']
            blank = stat['blank_lines']
            
            print(f"{lang:<12} {files:<6} {total:<8} {code:<8} {comments:<9} {blank:<6}")
            
            if lang != 'Filtered':
                total_files += files
                total_code += code
                total_lines += total
        
        print("-" * 60)
        print(f"{'TOTAL':<12} {total_files:<6} {total_lines:<8} {total_code:<8}")
        
        if not show_filtered and 'Filtered' in file_stats:
            print(f"\n💡 {file_stats['Filtered']} files were filtered out (use show_filtered=True to include)")
    
    @staticmethod
    def show_unknown_files(analyzer: LanguageProjectAnalyzer, project_path: str, limit: int = 20):
        """Show sample of files that are classified as 'Unknown'."""
        unknown_files = analyzer.get_unknown_files(project_path, limit * 2)  # Get more than needed
        
        if unknown_files:
            print(f"\n🔍 Unknown files (showing first {min(limit, len(unknown_files))}):")
            print("-" * 50)
            for i, file_path in enumerate(unknown_files[:limit]):
                file_name = os.path.basename(file_path)
                file_ext = Path(file_path).suffix
                rel_path = os.path.relpath(file_path, project_path)
                print(f"{i+1:2d}. {file_name} (ext: '{file_ext}') - {rel_path}")
            
            if len(unknown_files) > limit:
                print(f"... and {len(unknown_files) - limit} more unknown files")
        else:
            print(f"\n✅ No unknown files found!")


# Public API functions for external use
def analyze_project_languages(project_path: str, include_filtered: bool = False) -> Dict[str, int]:
    """Analyze programming languages in a project (file counts only)."""
    analyzer = LanguageProjectAnalyzer()
    return analyzer.analyze_project_languages(project_path, include_filtered)

def analyze_project_lines_of_code(project_path: str, include_filtered: bool = False) -> Dict[str, FileStats]:
    """Analyze lines of code by language in a project."""
    analyzer = LanguageProjectAnalyzer()
    return analyzer.analyze_project_lines_of_code(project_path, include_filtered)