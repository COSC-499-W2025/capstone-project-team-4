#!/usr/bin/env python3
"""
analyze_project_suitability.py - Analyze if a GitHub project is suitable for test data

Usage:
    python scripts/analyze_project_suitability.py <github_url>

Example:
    python scripts/analyze_project_suitability.py https://github.com/owner/project
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from collections import Counter


def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None


def clone_repository(repo_url, dest_dir):
    """Clone a git repository"""
    try:
        subprocess.run(
            ['git', 'clone', '--quiet', repo_url, dest_dir],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_total_commits(repo_dir):
    """Get total number of commits"""
    output = run_command('git log --oneline --all', cwd=repo_dir)
    if not output:
        return 0
    return len(output.split('\n'))


def get_contributors(repo_dir):
    """Get list of contributors with commit counts"""
    output = run_command('git shortlog -sn --all', cwd=repo_dir)
    if not output:
        return []

    contributors = []
    for line in output.split('\n'):
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) == 2:
                count = int(parts[0])
                name = parts[1]
                contributors.append({'name': name, 'commits': count})
    return contributors


def get_date_range(repo_dir):
    """Get first and last commit dates"""
    first_date = run_command(
        'git log --reverse --pretty=format:"%ad" --date=short',
        cwd=repo_dir
    )
    last_date = run_command(
        'git log --pretty=format:"%ad" --date=short',
        cwd=repo_dir
    )

    if first_date and last_date:
        first_date = first_date.split('\n')[0]
        last_date = last_date.split('\n')[0]
        return first_date, last_date

    return None, None


def calculate_duration(first_date, last_date):
    """Calculate duration in months between two dates"""
    try:
        date1 = datetime.strptime(first_date, "%Y-%m-%d")
        date2 = datetime.strptime(last_date, "%Y-%m-%d")
        days_diff = (date2 - date1).days
        months_diff = days_diff // 30
        return days_diff, months_diff
    except:
        return 0, 0


def analyze_languages(repo_dir):
    """Analyze languages used in the repository"""
    language_map = {
        'py': 'Python',
        'js': 'JavaScript',
        'ts': 'TypeScript',
        'jsx': 'JavaScript React',
        'tsx': 'TypeScript React',
        'java': 'Java',
        'go': 'Go',
        'rs': 'Rust',
        'cpp': 'C++',
        'c': 'C',
        'rb': 'Ruby',
        'php': 'PHP',
        'swift': 'Swift',
        'kt': 'Kotlin',
    }

    extensions = []
    for root, dirs, files in os.walk(repo_dir):
        # Skip .git directory
        if '.git' in root:
            continue

        for file in files:
            ext = Path(file).suffix.lstrip('.')
            if ext:
                extensions.append(ext)

    ext_counts = Counter(extensions)
    return ext_counts, language_map


def count_files(repo_dir):
    """Count total files (excluding .git)"""
    count = 0
    for root, dirs, files in os.walk(repo_dir):
        if '.git' in root:
            continue
        count += len(files)
    return count


def estimate_loc(repo_dir):
    """Estimate lines of code"""
    code_extensions = ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.c', '.cpp', '.rb']
    total_lines = 0

    for root, dirs, files in os.walk(repo_dir):
        # Skip certain directories
        if any(skip in root for skip in ['.git', 'node_modules', 'venv', '.venv', '__pycache__']):
            continue

        for file in files:
            if any(file.endswith(ext) for ext in code_extensions):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += len(f.readlines())
                except:
                    pass

    return total_lines


def check_dependencies(repo_dir):
    """Check what dependency files exist"""
    dependencies = []

    dep_files = {
        'package.json': 'Node.js/React',
        'requirements.txt': 'Python',
        'pyproject.toml': 'Python',
        'Pipfile': 'Python',
        'pom.xml': 'Java/Maven',
        'build.gradle': 'Java/Gradle',
        'go.mod': 'Go',
        'Cargo.toml': 'Rust',
        'Dockerfile': 'Docker',
    }

    repo_path = Path(repo_dir)
    for file, description in dep_files.items():
        if (repo_path / file).exists():
            dependencies.append({'file': file, 'description': description})

    # Check for GitHub Actions
    workflows_dir = repo_path / '.github' / 'workflows'
    if workflows_dir.exists():
        workflow_count = len(list(workflows_dir.glob('*.yml'))) + len(list(workflows_dir.glob('*.yaml')))
        if workflow_count > 0:
            dependencies.append({'file': f'.github/workflows ({workflow_count} workflows)', 'description': 'GitHub Actions'})

    return dependencies


def get_snapshot_points(repo_dir, total_commits):
    """Get suggested snapshot commit points"""
    snapshot1_num = max(5, total_commits * 20 // 100)
    snapshot2_num = total_commits * 60 // 100
    snapshot3_num = total_commits * 85 // 100

    commits = run_command('git log --reverse --oneline', cwd=repo_dir)
    if not commits:
        return []

    commit_lines = commits.split('\n')

    snapshots = []
    for i, num in enumerate([snapshot1_num, snapshot2_num, snapshot3_num], 1):
        if num < len(commit_lines):
            commit_line = commit_lines[num]
            snapshots.append({
                'number': i,
                'percentage': [20, 60, 85][i-1],
                'commit_num': num,
                'commit': commit_line
            })

    return snapshots


def assess_suitability(total_commits, contributor_count, loc):
    """Assess if the project is suitable"""
    warnings = []

    if total_commits < 50 or total_commits > 500:
        warnings.append("Commit count outside ideal range (50-500)")

    if contributor_count < 3:
        warnings.append("Not enough contributors (need 3+)")

    if loc > 0:
        if loc < 1000 or loc > 10000:
            warnings.append("LOC outside ideal range (1,000-10,000)")

    if len(warnings) == 0:
        return "SUITABLE", warnings
    elif len(warnings) <= 2:
        return "ACCEPTABLE", warnings
    else:
        return "NOT IDEAL", warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_project_suitability.py <github_url>")
        print()
        print("Example:")
        print("  python analyze_project_suitability.py https://github.com/owner/project")
        sys.exit(1)

    repo_url = sys.argv[1]
    repo_name = Path(repo_url).stem

    print("=" * 50)
    print(f"Analyzing: {repo_name}")
    print("=" * 50)
    print()

    # Create temp directory and clone
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / repo_name

        print("Cloning repository...")
        if not clone_repository(repo_url, repo_dir):
            print("Error: Failed to clone repository")
            sys.exit(1)

        print()
        print("Repository Analysis:")
        print("=" * 50)
        print()

        # 1. Commit count
        total_commits = get_total_commits(repo_dir)
        print(f"✓ Total Commits: {total_commits}")

        if total_commits < 50:
            print("  ⚠️  Warning: Less than 50 commits (need 50-500)")
        elif total_commits > 500:
            print("  ⚠️  Warning: More than 500 commits (might be too large)")
        else:
            print("  ✓ Good range (50-500)")
        print()

        # 2. Contributors
        contributors = get_contributors(repo_dir)
        contributor_count = len(contributors)

        print(f"✓ Contributors: {contributor_count}")
        for i, contrib in enumerate(contributors[:8]):
            print(f"  {contrib['commits']:6d}  {contrib['name']}")
        if len(contributors) > 8:
            print(f"  ... and {len(contributors) - 8} more")

        if contributor_count < 3:
            print("  ⚠️  Warning: Less than 3 contributors")
        elif contributor_count > 10:
            print("  ⚠️  Warning: More than 10 contributors (might be complex)")
        else:
            print("  ✓ Good range (3-10)")
        print()

        # 3. Date range
        first_date, last_date = get_date_range(repo_dir)
        if first_date and last_date:
            print(f"✓ Date Range: {first_date} to {last_date}")
            days_diff, months_diff = calculate_duration(first_date, last_date)
            print(f"  Duration: ~{months_diff} months ({days_diff} days)")

            if months_diff < 3:
                print("  ⚠️  Warning: Less than 3 months of history")
            else:
                print("  ✓ Good duration (3+ months)")
        print()

        # 4. Languages
        ext_counts, language_map = analyze_languages(repo_dir)
        print("✓ Languages Used:")
        for ext, count in ext_counts.most_common(10):
            lang_name = language_map.get(ext, f'.{ext}')
            print(f"  - {lang_name}: {count} files")
        print()

        # 5. Files and LOC
        file_count = count_files(repo_dir)
        print(f"✓ Total Files: {file_count}")

        loc = estimate_loc(repo_dir)
        if loc > 0:
            print(f"✓ Estimated LOC: ~{loc:,}")

            if loc < 1000:
                print("  ⚠️  Warning: Less than 1,000 LOC (might be too simple)")
            elif loc > 10000:
                print("  ⚠️  Warning: More than 10,000 LOC (might be too complex)")
            else:
                print("  ✓ Good size (1,000-10,000 LOC)")
        print()

        # 6. Dependencies
        dependencies = check_dependencies(repo_dir)
        if dependencies:
            print("✓ Dependencies Found:")
            for dep in dependencies:
                print(f"  - {dep['file']} ({dep['description']})")
        print()

        # 7. Suggested snapshot points
        snapshots = get_snapshot_points(repo_dir, total_commits)
        if snapshots:
            print("✓ Suggested Snapshot Points:")
            print()
            for snap in snapshots:
                stage = ['Foundation', 'Growth', 'Mature'][snap['number'] - 1]
                print(f"  Snapshot {snap['number']} ({stage} ~{snap['percentage']}%):")
                print(f"    {snap['commit']}")
                print()

        # 8. Suitability assessment
        print("=" * 50)
        print("SUITABILITY ASSESSMENT")
        print("=" * 50)

        assessment, warnings = assess_suitability(total_commits, contributor_count, loc)

        for warning in warnings:
            print(f"⚠️  {warning}")

        print()
        if assessment == "SUITABLE":
            print("✓✓✓ This project appears SUITABLE for test data! ✓✓✓")
        elif assessment == "ACCEPTABLE":
            print("✓ This project is ACCEPTABLE with minor concerns")
        else:
            print("✗ This project may NOT be ideal for test data")

        print()
        print("Next steps:")
        print(f"1. Clone with: git clone {repo_url}")
        print("2. Create snapshots with: python scripts/create_all_snapshots.py")


if __name__ == '__main__':
    main()
