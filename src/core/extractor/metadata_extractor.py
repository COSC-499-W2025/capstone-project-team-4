import os
import json
import magic
from datetime import datetime
from pathlib import Path

# Yeah... Po from Kung Fu Panda!!!!
import pandas as po
from tqdm import tqdm

# Import language analyzer components with consolidated configuration
from .language_parser import LanguageConfig, LanguageDetector, CommentDetector
from ..config.skill_mappings import get_language_config

# Load configuration from centralized YAML config
def _get_filter_config():
    """Get filtering configuration from centralized config."""
    config = get_language_config()
    skip_patterns = config.get('skip_patterns', {})
    limits = config.get('limits', {})
    
    return {
        'skip_directories': set(skip_patterns.get('skip_directories', [])),
        'skip_extensions': set(skip_patterns.get('skip_extensions', [])), 
        'skip_filenames': set(skip_patterns.get('skip_filenames', [])),
        'max_file_size': limits.get('max_file_size', 50 * 1024 * 1024),
        'min_file_size': limits.get('min_file_size', 1)
    }

def extract_metadata_enhanced(folder_path: str, use_existing_infrastructure: bool = True) -> po.DataFrame:
    """
    Enhanced metadata extraction with tree-sitter integration.
    
    Args:
        folder_path: Path to directory to analyze
        use_existing_infrastructure: Use existing analyzer infrastructure (default: True)
        
    Returns:
        DataFrame with enhanced metadata including tree-sitter analysis
    """
    if use_existing_infrastructure:
        # Use existing infrastructure properly
        from ..analyzer.file_analyzer import FileAnalyzer
        from .language_extractor import LanguageProjectAnalyzer
        
        # Initialize proper analyzer chain
        analyzer = LanguageProjectAnalyzer()
        results = []
        
        # Walk files using existing infrastructure
        file_count = 0
        with tqdm(desc="Enhanced metadata extraction", unit=" files") as pbar:
            for file_path in analyzer.file_walker.walk_source_files(folder_path):
                file_count += 1
                filename = os.path.basename(file_path)
                relative_path = os.path.relpath(file_path, folder_path)
                
                # Check if should analyze
                should_analyze = analyzer.file_walker.should_analyze_file(file_path)
                
                if not should_analyze:
                    # Skip filtered files in enhanced mode
                    continue
                
                try:
                    # Get comprehensive analysis
                    language = analyzer.file_analyzer.detect_language_by_extension(file_path)
                    
                    # Enhanced file analysis using proper methods
                    language, file_stats = analyzer.file_analyzer.analyze_single_file(file_path)
                    
                    # Build result with enhanced metadata
                    result = {
                        'filename': filename,
                        'path': relative_path,
                        'language': language,
                        'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                        'status': 'success'
                    }
                    
                    # Add file statistics if available
                    if file_stats:
                        result.update({
                            'total_lines': file_stats.total_lines,
                            'code_lines': file_stats.code_lines,
                            'comment_lines': file_stats.comment_lines,
                            'blank_lines': file_stats.blank_lines,
                            'comment_ratio': file_stats.comment_lines / max(file_stats.total_lines, 1),
                            'function_count': getattr(file_stats, 'functions', 0),
                            'class_count': getattr(file_stats, 'classes', 0),
                            'import_count': getattr(file_stats, 'imports', 0),
                            'complexity_score': getattr(file_stats, 'complexity_score', 0)
                        })
                        
                    results.append(result)
                    
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'path': relative_path,
                        'status': 'error',
                        'error': str(e)
                    })
                
                pbar.update(1)
                pbar.set_postfix({'processed': len(results), 'total_files': file_count})
        
        return po.DataFrame(results)
    else:
        # Fallback to enhanced version of original method
        df, _ = parse_metadata(folder_path, include_filtered=False)
        return df


def should_skip_file(file_path: str, file_name: str, filter_config: dict = None) -> tuple[bool, str]:
    """
    Determines if a file should be skipped using centralized configuration.
    
    Args:
        file_path: Full path to the file
        file_name: Just the filename
        filter_config: Pre-loaded filter configuration (optional)
    
    Returns:
        tuple: (should_skip: bool, reason: str)
    """
    if filter_config is None:
        filter_config = _get_filter_config()
    
    path_obj = Path(file_path)
    
    # Check file extension
    if path_obj.suffix.lower() in filter_config['skip_extensions']:
        return True, f"skipped extension: {path_obj.suffix}"
    
    # Check filename
    if file_name.lower() in [f.lower() for f in filter_config['skip_filenames']]:
        return True, f"skipped filename: {file_name}"
    
    # Check if file is in a skipped directory
    parts = path_obj.parts
    for part in parts:
        if part in filter_config['skip_directories']:
            return True, f"skipped directory: {part}"
    
    # Check file size
    try:
        file_size = os.path.getsize(file_path)
        if file_size > filter_config['max_file_size']:
            return True, f"file too large: {file_size} bytes"
        if file_size < filter_config['min_file_size']:
            return True, f"file too small: {file_size} bytes"
    except OSError:
        pass
    
    return False, ""


def parse_metadata(folder_path: str = "", include_filtered: bool = False):
    """
    Opens up a folder from a recently extracted zip file and lists the file type, file size, and created/modified
    timestamps

    Args:
        folder_path: the path to the directory/folder to be parsed (default "")
        include_filtered: if True, includes filtered files with their skip reason (default False)
    
    Returns:
        tuple: (dataframe, project_root_path)
    """
    results = []
    filtered_count = 0
    progress_bar = tqdm(desc="Parsing metadata", unit=" files")
    
    # Convert folder_path to Path object for easier manipulation
    base_path = Path(folder_path).resolve()
    
    # Initialize language analyzer components with centralized config
    from ..analyzer.file_analyzer import FileAnalyzer
    from .language_extractor import FileWalker
    
    config = LanguageConfig()
    language_detector = LanguageDetector(config)
    comment_detector = CommentDetector()
    file_walker = FileWalker(language_detector)
    file_analyzer = FileAnalyzer(language_detector, comment_detector)
    
    # Load filter configuration once for efficiency
    filter_config = _get_filter_config()

    for root, dirs, files in os.walk(folder_path):
        # Skip entire directories using centralized configuration
        dirs[:] = [d for d in dirs if d not in filter_config['skip_directories']]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if file should be skipped using pre-loaded config
            should_skip, skip_reason = should_skip_file(file_path, file, filter_config)
            
            if should_skip:
                filtered_count += 1
                if include_filtered:
                    # Convert absolute path to relative path
                    absolute_path = Path(file_path).resolve()
                    try:
                        relative_path = absolute_path.relative_to(base_path)
                    except ValueError:
                        relative_path = Path(file)
                    
                    result = {
                        "filename": file,
                        "path": str(relative_path),
                        "file_type": "FILTERED",
                        "language": "Filtered",
                        "file_size": None,
                        "created_timestamp": None,
                        "last_modified": None,
                        "lines_of_code": None,
                        "skip_reason": skip_reason,
                        "status": "filtered"
                    }
                    results.append(result)
                continue
            
            try:
                file_type = magic.from_file(file_path, mime=True)
                file_size = os.path.getsize(file_path)
                created_timestamp = os.path.getctime(file_path)
                modified_timestamp = os.path.getmtime(file_path)

                # Enhanced language detection and analysis
                language = file_analyzer.detect_language_by_extension(file_path)
                
                # Enhanced file analysis with tree-sitter if available
                file_stats = None
                ast_metadata = {}
                comment_analysis = {}
                
                try:
                    # Use the correct analyze_single_file method
                    detected_language, file_stats = file_analyzer.analyze_single_file(file_path)
                    lines_of_code = file_stats.code_lines if file_stats else None
                    
                    # Update language from actual analysis
                    if detected_language and detected_language != "Unknown":
                        language = detected_language
                        
                except Exception as analysis_error:
                    print(f"[WARN] Analysis failed for {file_path}: {analysis_error}")
                    # Final fallback
                    try:
                        file_stats = file_analyzer.count_lines_of_code(file_path, language)
                        lines_of_code = file_stats.code_lines if file_stats else None
                    except Exception as loc_error:
                        print(f"[WARN] Could not calculate LOC for {file_path}: {loc_error}")
                        lines_of_code = None

                # Convert absolute path to relative path from extracted directory
                absolute_path = Path(file_path).resolve()
                try:
                    relative_path = absolute_path.relative_to(base_path)
                except ValueError:
                    relative_path = Path(file)

                # Build comprehensive result with enhanced metadata
                result = {
                    "filename": file,
                    "path": str(relative_path),
                    "file_type": file_type,
                    "language": language,
                    "file_size": file_size,
                    "created_timestamp": created_timestamp,
                    "last_modified": modified_timestamp,
                    "lines_of_code": lines_of_code,
                    "status": "success"
                }
                
                # Add enhanced metadata if available
                if file_stats:
                    result.update({
                        "total_lines": file_stats.total_lines,
                        "comment_lines": file_stats.comment_lines,
                        "blank_lines": file_stats.blank_lines,
                        "comment_ratio": file_stats.comment_lines / max(file_stats.total_lines, 1)
                    })
                
                # Add AST-based metadata (tree-sitter enhanced)
                if ast_metadata:
                    result.update({
                        "function_count": ast_metadata.get('function_count', 0),
                        "class_count": ast_metadata.get('class_count', 0),
                        "import_count": ast_metadata.get('import_count', 0),
                        "max_nesting_depth": ast_metadata.get('max_nesting_depth', 0),
                        "has_documentation": ast_metadata.get('has_documentation', False),
                        "complexity_indicators": ast_metadata.get('complexity_score', 0)
                    })
                
                # Add detailed comment analysis
                if comment_analysis:
                    result.update({
                        "inline_comments": comment_analysis.get('inline_count', 0),
                        "block_comments": comment_analysis.get('block_count', 0),
                        "docstring_count": comment_analysis.get('docstring_count', 0),
                        "todo_comments": comment_analysis.get('todo_count', 0)
                    })
                results.append(result)
            except Exception as exception:
                # Convert absolute path to relative path for errors too
                absolute_path = Path(file_path).resolve()
                try:
                    relative_path = absolute_path.relative_to(base_path)
                except ValueError:
                    relative_path = Path(file)
                
                result = {
                    "filename": file,
                    "path": str(relative_path),
                    "file_type": "ERROR",
                    "language": "Unknown",
                    "file_size": None,
                    "created_timestamp": None,
                    "last_modified": None,
                    "lines_of_code": None,  # Add LOC field for errors
                    "error": str(exception),
                    "status": "error"
                }
                results.append(result)

            # Progress bar update
            progress_bar.set_postfix({
                "folder": os.path.basename(root),
                "filtered": filtered_count
            })
            progress_bar.update()

    progress_bar.close()
    print(f"Filtered out {filtered_count} files")
    
    dataframe = po.DataFrame(results)
    project_root = str(base_path)
    return dataframe, project_root


def save_metadata_json(dataframe: po.DataFrame, output_filename: str = "metadata.json", project_root: str = None) -> str:
    """
    Converts metadata dataframe to clean JSON format and saves to outputs directory.
    
    Args:
        dataframe: DataFrame containing metadata from parse_metadata()
        output_filename: Name of output JSON file (default: "metadata.json")
        project_root: Absolute path to the project root directory
    
    Returns:
        str: Path to the saved JSON file
    """
    # Create outputs directory at project root level, not in src/
    outputs_dir = Path.cwd() / "outputs"  # Changed from Path(__file__).parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # Clean and format the data
    cleaned_data = []
    
    for _, row in dataframe.iterrows():
        # Handle pandas NaN values properly
        file_size = row.get('file_size')
        if file_size is not None and not po.isna(file_size):
            file_size = int(file_size)
        else:
            file_size = None
            
        created_ts = row.get('created_timestamp')
        if created_ts is not None and not po.isna(created_ts):
            created_ts = float(created_ts)
        else:
            created_ts = None
            
        last_mod = row.get('last_modified')
        if last_mod is not None and not po.isna(last_mod):
            last_mod = float(last_mod)
        else:
            last_mod = None
            
        # Handle lines of code
        lines_of_code = row.get('lines_of_code')
        if lines_of_code is not None and not po.isna(lines_of_code):
            lines_of_code = int(lines_of_code)
        else:
            lines_of_code = None
            
        # Handle language field
        language = row.get('language')
        if language is not None and not po.isna(language):
            language = str(language)
        else:
            language = "Unknown"
        
        # Create clean record with all fields from parse_metadata
        record = {
            "filename": str(row['filename']),
            "path": str(row['path']),
            "file_type": str(row['file_type']),
            "language": language,  # Add language field
            "file_size": file_size,
            "lines_of_code": lines_of_code,  # Add LOC field
            "created_timestamp": created_ts,
            "last_modified": last_mod,
            "status": str(row.get('status', 'success'))
        }
        
        # Add error information if present
        if 'error' in row and row['error'] is not None and not po.isna(row['error']):
            record["error"] = str(row['error'])
        
        # Add skip reason if present (for filtered files)
        if 'skip_reason' in row and row['skip_reason'] is not None and not po.isna(row['skip_reason']):
            record["skip_reason"] = str(row['skip_reason'])
        
        cleaned_data.append(record)
    
    # Calculate statistics including LOC
    successful_files = [r for r in cleaned_data if r["status"] == "success" and r["file_size"] is not None]
    filtered_files = [r for r in cleaned_data if r["status"] == "filtered"]
    error_files = [r for r in cleaned_data if r["status"] == "error"]
    
    total_size = sum(r["file_size"] for r in successful_files) if successful_files else 0
    avg_size = total_size / len(successful_files) if successful_files else 0
    
    # Calculate total LOC
    files_with_loc = [r for r in successful_files if r["lines_of_code"] is not None]
    total_loc = sum(r["lines_of_code"] for r in files_with_loc) if files_with_loc else 0
    avg_loc = total_loc / len(files_with_loc) if files_with_loc else 0
    
    # Create final JSON structure with metadata
    json_output = {
        "metadata": {
            "generated_at": datetime.now().timestamp(),
            "total_files": len(cleaned_data),
            "successful_parses": len(successful_files),
            "failed_parses": len(error_files),
            "filtered_files": len(filtered_files),
            "total_size_bytes": total_size,
            "average_file_size_bytes": round(avg_size, 2),
            "total_lines_of_code": total_loc,  # Add total LOC
            "average_lines_of_code": round(avg_loc, 2),  # Add average LOC
            "files_with_loc": len(files_with_loc),  # Files that had LOC calculated
            "schema_version": "2.3"  # Updated version to include LOC
        },
        "project_root": project_root,
        "files": cleaned_data
    }
    
    # Save to outputs directory
    output_path = outputs_dir / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        
        print(f"Metadata saved to: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Error saving metadata JSON: {e}")
        raise

