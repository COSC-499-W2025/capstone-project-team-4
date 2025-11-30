"""
Combined utilities for common functionality.
"""
import json
import typer
from datetime import datetime
from pathlib import Path

# Logging functionality
LOG_FILE = Path(__file__).resolve().parent / "../data/consent_log.json"

def log_event(service_name: str, status: str):
    """Log user consent decisions with timestamps."""
    log_entry = {
        "service": service_name,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []

    logs.append(log_entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(logs, indent=2))


# Pretty printing functionality
def readable_size(num_bytes):
    """Convert bytes to MB/GB for readability."""
    try:
        if num_bytes >= 1_000_000_000:
            return f"{num_bytes / 1_000_000_000:.2f} GB"
        elif num_bytes >= 1_000_000:
            return f"{num_bytes / 1_000_000:.2f} MB"
        elif num_bytes >= 1_000:
            return f"{num_bytes / 1_000:.2f} KB"
        return f"{num_bytes} bytes"
    except:
        return "?"


def pretty_print_json(file_name: str, data: dict, raw: bool = False):
    """
    Pretty prints known JSON files in a human-friendly format.
    Falls back to raw JSON dump when unknown or when raw=True.
    """
    if raw:
        typer.echo(json.dumps(data, indent=2))
        return

    # Resume item formatting
    if file_name == "resume_item.json":
        typer.secho("\n📘 Resume Item\n", fg=typer.colors.BLUE, bold=True)
        title = data.get("title", "")
        highlights = data.get("highlights", [])
        typer.secho("Title:", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"  {title}\n")
        typer.secho("Highlights:", fg=typer.colors.GREEN, bold=True)
        for h in highlights:
            typer.echo(f"  {h}")
        typer.echo("")
        return

    # Skill extraction formatting  
    if file_name == "skill_extract.json":
        typer.secho("\n🧠 Resume Skills\n", fg=typer.colors.MAGENTA, bold=True)
        
        # Handle different skill extraction formats
        skills_flat = data.get("skills_flat", [])
        if skills_flat:
            typer.secho("📋 All Skills:", fg=typer.colors.CYAN, bold=True)
            for skill in skills_flat[:15]:  # Show top 15
                typer.echo(f"  • {skill}")
            if len(skills_flat) > 15:
                typer.echo(f"  ... and {len(skills_flat) - 15} more skills")
            typer.echo("")
        
        # Show categorized skills
        skill_categories = {k: v for k, v in data.items() 
                           if k not in ["languages", "frameworks", "skills_flat"] and isinstance(v, list)}
        
        if skill_categories:
            typer.secho("📚 Skills by Category:", fg=typer.colors.YELLOW, bold=True)
            for category, skills in skill_categories.items():
                if skills:  # Only show categories with skills
                    typer.secho(f"  {category}:", fg=typer.colors.GREEN)
                    for skill in skills[:5]:  # Limit per category
                        typer.echo(f"    • {skill}")
                    if len(skills) > 5:
                        typer.echo(f"    ... and {len(skills) - 5} more")
            typer.echo("")
        
        # Show detected languages and frameworks
        languages = data.get("languages", [])
        if languages:
            typer.secho("💻 Languages Detected:", fg=typer.colors.BLUE, bold=True)
            for lang in languages:
                typer.echo(f"  • {lang}")
            typer.echo("")
        
        frameworks = data.get("frameworks", [])
        if frameworks:
            typer.secho("🛠️  Frameworks Detected:", fg=typer.colors.RED, bold=True)
            for framework in frameworks:
                typer.echo(f"  • {framework}")
            typer.echo("")
        
        # Show summary
        total_skills = len(skills_flat) if skills_flat else sum(len(v) for v in skill_categories.values() if isinstance(v, list))
        if total_skills > 0:
            typer.secho(f"📊 Total Skills Found: {total_skills}", fg=typer.colors.WHITE, bold=True)
        
        return

    # Contributors formatting
    if file_name == "contributors.json":
        typer.secho("\n👥 Project Contributors\n", fg=typer.colors.BLUE, bold=True)
        
        # Handle both array format and object with "value" key
        if isinstance(data, list):
            contributors = data
        else:
            contributors = data.get("value", data.get("contributors", []))
        total_contributors = len(contributors)
        
        if total_contributors == 0:
            typer.echo("  No contributors found.")
            return
            
        typer.secho(f"📊 Total Contributors: {total_contributors}", fg=typer.colors.WHITE, bold=True)
        typer.echo("")
        
        for i, contrib in enumerate(contributors, 1):
            name = contrib.get("name", "Unknown")
            email = contrib.get("primary_email", "No email")
            commits = contrib.get("commits", 0)
            percent = contrib.get("percent", 0)
            lines_added = contrib.get("total_lines_added", 0)
            lines_deleted = contrib.get("total_lines_deleted", 0)
            files_modified = contrib.get("files_modified", {})
            
            typer.secho(f"{i}. {name}", fg=typer.colors.CYAN, bold=True)
            typer.echo(f"   📧 Email: {email}")
            typer.echo(f"   📝 Commits: {commits} ({percent:.1f}%)")
            typer.echo(f"   📊 Lines: +{lines_added} / -{lines_deleted} (net: {lines_added - lines_deleted:+})")
            typer.echo(f"   📁 Files touched: {len(files_modified)}")
            
            if files_modified:
                # Show top 5 most modified files
                top_files = sorted(files_modified.items(), key=lambda x: x[1], reverse=True)[:5]
                typer.secho("   🔝 Most modified files:", fg=typer.colors.YELLOW)
                for file_name, changes in top_files:
                    typer.echo(f"      • {file_name} ({changes} changes)")
                if len(files_modified) > 5:
                    typer.echo(f"      ... and {len(files_modified) - 5} more files")
            typer.echo("")
        
        return

    # Metadata formatting
    if file_name == "metadata.json":
        typer.secho("\n📋 Project Metadata\n", fg=typer.colors.GREEN, bold=True)
        
        metadata = data.get("metadata", {})
        project_root = data.get("project_root", "Unknown")
        files = data.get("files", [])
        
        # Project overview
        typer.secho("📁 Project Overview:", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"   Path: {project_root}")
        typer.echo(f"   Total files: {metadata.get('total_files', len(files))}")
        typer.echo(f"   Total size: {readable_size(metadata.get('total_size_bytes', 0))}")
        typer.echo(f"   Average file size: {readable_size(metadata.get('average_file_size_bytes', 0))}")
        typer.echo(f"   Project duration: {metadata.get('duration_days', 0):.1f} days")
        typer.echo(f"   Collaborative: {'Yes' if metadata.get('collaborative', False) else 'No'}")
        typer.echo("")
        
        # Language breakdown
        if files:
            languages = {}
            file_types = {}
            
            for file_info in files:
                lang = file_info.get("language", "Unknown")
                file_type = file_info.get("file_type", "Unknown")
                
                languages[lang] = languages.get(lang, 0) + 1
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Show top languages
            if languages:
                typer.secho("💻 Languages:", fg=typer.colors.MAGENTA, bold=True)
                sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
                for lang, count in sorted_langs[:10]:
                    percentage = (count / len(files)) * 100
                    typer.echo(f"   • {lang}: {count} files ({percentage:.1f}%)")
                if len(sorted_langs) > 10:
                    typer.echo(f"   ... and {len(sorted_langs) - 10} more languages")
                typer.echo("")
            
            # Show file status summary
            status_counts = {}
            for file_info in files:
                status = file_info.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                typer.secho("✅ Processing Status:", fg=typer.colors.YELLOW, bold=True)
                for status, count in status_counts.items():
                    percentage = (count / len(files)) * 100
                    status_emoji = "✅" if status == "success" else "⚠️" if status == "filtered" else "❌"
                    typer.echo(f"   {status_emoji} {status.title()}: {count} files ({percentage:.1f}%)")
                typer.echo("")
        
        return

    # Complexity analysis formatting
    if file_name == "complexity.json":
        typer.secho("\n📊 Code Complexity Analysis\n", fg=typer.colors.CYAN, bold=True)
        
        project_root = data.get("project_root", "Unknown")
        functions = data.get("functions", [])
        
        if not functions:
            typer.echo("  No functions analyzed.")
            return
        
        # Overview
        typer.secho("📁 Project Overview:", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"   Path: {project_root}")
        typer.echo(f"   Functions analyzed: {len(functions)}")
        
        # Calculate statistics
        complexities = [f.get("cyclomatic_complexity", 0) for f in functions]
        if complexities:
            avg_complexity = sum(complexities) / len(complexities)
            max_complexity = max(complexities)
            min_complexity = min(complexities)
            
            typer.echo(f"   Average complexity: {avg_complexity:.2f}")
            typer.echo(f"   Complexity range: {min_complexity} - {max_complexity}")
        typer.echo("")
        
        # Categorize by complexity
        simple = [f for f in functions if f.get("cyclomatic_complexity", 0) <= 5]
        moderate = [f for f in functions if 5 < f.get("cyclomatic_complexity", 0) <= 10]
        complex_funcs = [f for f in functions if f.get("cyclomatic_complexity", 0) > 10]
        
        typer.secho("🚦 Complexity Distribution:", fg=typer.colors.WHITE, bold=True)
        typer.secho(f"   🟢 Simple (1-5): {len(simple)} functions ({len(simple)/len(functions)*100:.1f}%)", fg=typer.colors.GREEN)
        typer.secho(f"   🟡 Moderate (6-10): {len(moderate)} functions ({len(moderate)/len(functions)*100:.1f}%)", fg=typer.colors.YELLOW)
        typer.secho(f"   🔴 Complex (11+): {len(complex_funcs)} functions ({len(complex_funcs)/len(functions)*100:.1f}%)", fg=typer.colors.RED)
        typer.echo("")
        
        # Show most complex functions
        if complex_funcs:
            typer.secho("🔴 Most Complex Functions:", fg=typer.colors.RED, bold=True)
            sorted_complex = sorted(complex_funcs, key=lambda x: x.get("cyclomatic_complexity", 0), reverse=True)[:5]
            for func in sorted_complex:
                file_path = func.get("file_path", "").replace(project_root, "").lstrip("\\").lstrip("/")
                name = func.get("name", "Unknown")
                complexity = func.get("cyclomatic_complexity", 0)
                start_line = func.get("start_line", 0)
                typer.echo(f"   • {name} (complexity: {complexity}) - {file_path}:{start_line}")
            typer.echo("")
        
        # Show functions by file
        files_functions = {}
        for func in functions:
            file_path = func.get("file_path", "").replace(project_root, "").lstrip("\\").lstrip("/")
            if file_path not in files_functions:
                files_functions[file_path] = []
            files_functions[file_path].append(func)
        
        if files_functions:
            typer.secho("📁 Functions by File:", fg=typer.colors.MAGENTA, bold=True)
            for file_path, file_functions in list(files_functions.items())[:5]:  # Show top 5 files
                file_avg_complexity = sum(f.get("cyclomatic_complexity", 0) for f in file_functions) / len(file_functions)
                typer.secho(f"   📄 {file_path}", fg=typer.colors.CYAN)
                typer.echo(f"      Functions: {len(file_functions)}, Avg complexity: {file_avg_complexity:.2f}")
                
                # Show top 3 most complex functions in this file
                sorted_file_funcs = sorted(file_functions, key=lambda x: x.get("cyclomatic_complexity", 0), reverse=True)[:3]
                for func in sorted_file_funcs:
                    name = func.get("name", "Unknown")
                    complexity = func.get("cyclomatic_complexity", 0)
                    start_line = func.get("start_line", 0)
                    color = typer.colors.RED if complexity > 10 else typer.colors.YELLOW if complexity > 5 else typer.colors.GREEN
                    typer.secho(f"        • {name} (complexity: {complexity}, line: {start_line})", fg=color)
            
            if len(files_functions) > 5:
                typer.echo(f"      ... and {len(files_functions) - 5} more files")
        
        return

    # Framework detection formatting
    if file_name == "framework_detection.json":
        typer.secho("\n🛠️ Framework Detection Results\n", fg=typer.colors.MAGENTA, bold=True)
        
        project_root = data.get("project_root", "Unknown")
        rules_version = data.get("rules_version", "Unknown")
        frameworks = data.get("frameworks", {})
        
        # Overview
        typer.secho("📁 Project Overview:", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"   Path: {project_root}")
        typer.echo(f"   Rules version: {rules_version}")
        
        total_frameworks = sum(len(fw_list) for fw_list in frameworks.values())
        typer.echo(f"   Total frameworks detected: {total_frameworks}")
        typer.echo("")
        
        if not frameworks:
            typer.echo("  No frameworks detected.")
            return
        
        # Show frameworks by folder
        for folder_path, fw_list in frameworks.items():
            if not fw_list:
                continue
                
            folder_display = "Root" if folder_path == "." else folder_path
            typer.secho(f"📂 {folder_display}:", fg=typer.colors.CYAN, bold=True)
            
            # Sort frameworks by confidence
            sorted_frameworks = sorted(fw_list, key=lambda x: x.get("confidence", 0), reverse=True)
            
            for fw in sorted_frameworks:
                name = fw.get("name", "Unknown")
                confidence = fw.get("confidence", 0)
                signals = fw.get("signals", [])
                
                # Color code by confidence
                if confidence >= 0.8:
                    color = typer.colors.GREEN
                    emoji = "🟢"
                elif confidence >= 0.5:
                    color = typer.colors.YELLOW
                    emoji = "🟡"
                else:
                    color = typer.colors.RED
                    emoji = "🔴"
                
                typer.secho(f"   {emoji} {name}", fg=color, bold=True)
                typer.echo(f"      Confidence: {confidence:.1%}")
                typer.echo(f"      Detection signals: {len(signals)}")
                
                # Show first few signals
                if signals:
                    signal_preview = ", ".join(signals[:3])
                    if len(signals) > 3:
                        signal_preview += f" ... (+{len(signals) - 3} more)"
                    typer.echo(f"      Signals: {signal_preview}")
                
            typer.echo("")
        
        return

    # Language analysis formatting
    if file_name == "language_analysis.json":
        typer.secho("\n📊 Language Analysis Results\n", fg=typer.colors.MAGENTA, bold=True)
        
        project_path = data.get("project_path", "Unknown")
        file_counts = data.get("file_counts", {})
        lines_of_code = data.get("lines_of_code", {})
        
        # Overview
        typer.secho("📁 Project Overview:", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"   Path: {project_path}")
        
        total_files = sum(file_counts.values())
        total_lines = sum(lang_data.get("total_lines", 0) for lang_data in lines_of_code.values())
        total_code_lines = sum(lang_data.get("code_lines", 0) for lang_data in lines_of_code.values())
        
        typer.echo(f"   Total files: {total_files}")
        typer.echo(f"   Total lines: {total_lines:,}")
        typer.echo(f"   Total code lines: {total_code_lines:,}")
        typer.echo("")
        
        # Language breakdown
        typer.secho("🔤 Languages Detected:", fg=typer.colors.CYAN, bold=True)
        
        # Sort by total code lines (descending)
        languages_sorted = sorted(lines_of_code.items(), 
                                key=lambda x: x[1].get("code_lines", 0), 
                                reverse=True)
        
        for language, lang_data in languages_sorted:
            files = lang_data.get("files", 0)
            total_lines = lang_data.get("total_lines", 0)
            code_lines = lang_data.get("code_lines", 0)
            comment_lines = lang_data.get("comment_lines", 0)
            blank_lines = lang_data.get("blank_lines", 0)
            
            # Choose emoji based on language
            lang_emojis = {
                "Python": "🐍", "JavaScript": "🟨", "TypeScript": "🔷",
                "Java": "☕", "C++": "⚡", "C": "🔧", "C#": "💙",
                "HTML": "🌐", "CSS": "🎨", "JSON": "📋",
                "YAML": "⚙️", "Markdown": "📝", "Text": "📄",
                "Shell": "🐚", "PowerShell": "💻", "SQL": "🗄️",
                "Go": "🐹", "Rust": "🦀", "Ruby": "💎",
                "PHP": "🐘", "INI": "⚙️", "Unknown": "❓"
            }
            emoji = lang_emojis.get(language, "📄")
            
            # Color code by code lines
            if code_lines > 1000:
                color = typer.colors.GREEN
            elif code_lines > 100:
                color = typer.colors.YELLOW
            else:
                color = typer.colors.WHITE
                
            typer.secho(f"   {emoji} {language}", fg=color, bold=True)
            typer.echo(f"      Files: {files}")
            typer.echo(f"      Total lines: {total_lines:,}")
            typer.echo(f"      Code lines: {code_lines:,}")
            
            if comment_lines > 0:
                comment_ratio = (comment_lines / total_lines * 100) if total_lines > 0 else 0
                typer.echo(f"      Comments: {comment_lines:,} ({comment_ratio:.1f}%)")
            
            if blank_lines > 0:
                typer.echo(f"      Blank lines: {blank_lines:,}")
            
            typer.echo("")
        
        return

    # Default: raw JSON
    typer.echo(json.dumps(data, indent=2))