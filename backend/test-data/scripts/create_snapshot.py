#!/usr/bin/env python3
"""
create_snapshot.py - Create test data snapshots from a git repository

Usage:
    python scripts/create_snapshot.py <project_dir> <commit_hash> <snapshot_name>

Example:
    python scripts/create_snapshot.py demo-project-full abc123 code-collab-proj-v1-foundation
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import zipfile


def run_command(cmd, cwd=None, capture=True):
    """Run a shell command and return output"""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, cwd=cwd, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def get_commit_info(project_dir, commit_hash):
    """Get information about a specific commit"""
    date = run_command(
        f'git show --quiet --format="%ad" --date=short {commit_hash}',
        cwd=project_dir
    )
    author = run_command(
        f'git show --quiet --format="%an" {commit_hash}',
        cwd=project_dir
    )
    message = run_command(
        f'git show --quiet --format="%s" {commit_hash}',
        cwd=project_dir
    )
    return {
        'date': date,
        'author': author,
        'message': message
    }


def get_snapshot_stats(project_dir):
    """Get statistics about the snapshot"""
    commit_count = len(run_command('git log --oneline', cwd=project_dir).split('\n'))
    contributor_count = len(run_command('git shortlog -sn --all', cwd=project_dir).split('\n'))

    # Count files (excluding .git)
    file_count = 0
    for root, dirs, files in os.walk(project_dir):
        # Skip .git directory
        if '.git' in root:
            continue
        file_count += len(files)

    return {
        'commits': commit_count,
        'contributors': contributor_count,
        'files': file_count
    }


def clean_build_artifacts(project_dir):
    """Remove build artifacts but keep .git directory"""
    artifacts = [
        'node_modules',
        'venv',
        '.venv',
        '__pycache__',
        '.pytest_cache',
        'dist',
        'build',
        '.next',
        'out',
        '.tox',
        'htmlcov',
        '.coverage',
        '*.egg-info'
    ]

    for artifact in artifacts:
        # Handle wildcards
        if '*' in artifact:
            for path in Path(project_dir).rglob(artifact.replace('*', '')):
                if path.exists():
                    shutil.rmtree(path, ignore_errors=True)
        else:
            artifact_path = Path(project_dir) / artifact
            if artifact_path.exists():
                if artifact_path.is_dir():
                    shutil.rmtree(artifact_path, ignore_errors=True)
                else:
                    artifact_path.unlink()

    # Remove .pyc files
    for pyc_file in Path(project_dir).rglob('*.pyc'):
        pyc_file.unlink()


def create_zip(source_dir, output_file, exclude_patterns=None):
    """Create a ZIP file from a directory"""
    if exclude_patterns is None:
        exclude_patterns = ['*.pyc', '__pycache__', 'node_modules', '*.venv', 'venv']

    def should_exclude(path):
        """Check if path should be excluded"""
        path_str = str(path)
        for pattern in exclude_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        return False

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        source_path = Path(source_dir)
        for file_path in source_path.rglob('*'):
            if should_exclude(file_path):
                continue

            # Get relative path for the zip archive
            arcname = file_path.relative_to(source_path.parent)

            if file_path.is_file():
                zipf.write(file_path, arcname)


def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}TB"


def main():
    # Check arguments
    if len(sys.argv) != 4:
        print("Usage: python create_snapshot.py <project_dir> <commit_hash> <snapshot_name>")
        print()
        print("Arguments:")
        print("  project_dir   - Path to the git repository")
        print("  commit_hash   - Git commit hash to create snapshot at")
        print("  snapshot_name - Name for the snapshot (e.g., code-collab-proj-v1-foundation)")
        print()
        print("Example:")
        print("  python create_snapshot.py demo-project-full abc123 code-collab-proj-v1-foundation")
        sys.exit(1)

    project_dir = sys.argv[1]
    commit_hash = sys.argv[2]
    snapshot_name = sys.argv[3]

    # Get absolute paths
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    output_dir = project_root / 'backend' / 'test-data' / 'code-collab-proj-snapshots'

    # Validate project directory
    project_path = Path(project_dir)
    if not project_path.exists():
        print(f"Error: Project directory '{project_dir}' does not exist")
        sys.exit(1)

    git_dir = project_path / '.git'
    if not git_dir.exists():
        print(f"Error: '{project_dir}' is not a git repository")
        sys.exit(1)

    # Validate commit exists
    try:
        run_command(f'git cat-file -e {commit_hash}^{{commit}}', cwd=project_dir)
    except:
        print(f"Error: Commit '{commit_hash}' not found in repository")
        sys.exit(1)

    print(f"Creating snapshot '{snapshot_name}' at commit {commit_hash}...")
    print()

    # Get commit info
    commit_info = get_commit_info(project_dir, commit_hash)
    print("Commit Info:")
    print(f"  Date: {commit_info['date']}")
    print(f"  Author: {commit_info['author']}")
    print(f"  Message: {commit_info['message']}")
    print()

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Working in temporary directory: {temp_dir}")

        snapshot_dir = Path(temp_dir) / 'code-collab-proj'

        # Clone to specific commit
        print("Cloning repository to snapshot point...")
        run_command(
            f'git clone --quiet --no-hardlinks "file://{project_path.absolute()}" "{snapshot_dir}"',
            capture=False
        )

        # Reset to target commit
        print(f"Resetting to commit {commit_hash}...")
        run_command(f'git reset --hard {commit_hash} --quiet', cwd=snapshot_dir, capture=False)

        # Clean build artifacts
        print("Cleaning build artifacts...")
        clean_build_artifacts(snapshot_dir)

        # Get statistics
        stats = get_snapshot_stats(snapshot_dir)
        print()
        print("Snapshot Statistics:")
        print(f"  Commits: {stats['commits']}")
        print(f"  Contributors: {stats['contributors']}")
        print(f"  Files: {stats['files']}")
        print()

        # Create ZIP
        print("Creating ZIP archive...")
        output_file = output_dir / f"{snapshot_name}.zip"
        output_dir.mkdir(parents=True, exist_ok=True)

        create_zip(temp_dir, output_file)

        # Get ZIP size
        zip_size = format_size(output_file.stat().st_size)

    print()
    print("✓ Successfully created snapshot!")
    print()
    print("Output:")
    print(f"  File: {output_file}")
    print(f"  Size: {zip_size}")
    print()
    print("Verification commands:")
    print("  # Check git history exists")
    print(f'  unzip -l "{output_file}" | grep -c ".git/"')
    print()
    print("  # Extract and inspect")
    print(f'  cd /tmp && unzip -q "{output_file}"')
    print("  cd code-collab-proj && git log --oneline | head -10")
    print()


if __name__ == '__main__':
    main()
