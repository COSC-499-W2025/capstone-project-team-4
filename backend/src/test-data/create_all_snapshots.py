#!/usr/bin/env python3
"""
create_all_snapshots.py - Create all three test data snapshots from a git repository

This script automatically:
1. Analyzes the project to find suitable snapshot points
2. Creates 3 snapshots at 20%, 60%, and 85% of commit history
3. Provides information for updating snapshots.json

Usage:
    python scripts/create_all_snapshots.py <project_dir>

Example:
    python scripts/create_all_snapshots.py demo-project-full
"""

import os
import sys
import subprocess
from pathlib import Path


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
        print(f"Error: {e.stderr}")
        return None


def get_project_info(project_dir):
    """Get basic information about the project"""
    info = {}

    # Get project name from git remote
    remote_url = run_command('git remote get-url origin 2>/dev/null || echo "unknown"', cwd=project_dir)
    if remote_url and remote_url != "unknown":
        info['name'] = Path(remote_url).stem.replace('.git', '')
        info['url'] = remote_url
    else:
        info['name'] = Path(project_dir).name
        info['url'] = 'unknown'

    # Get commit count
    commits_output = run_command('git log --oneline --all', cwd=project_dir)
    info['total_commits'] = len(commits_output.split('\n')) if commits_output else 0

    # Get contributor count
    contributors_output = run_command('git shortlog -sn --all', cwd=project_dir)
    info['contributors'] = len(contributors_output.split('\n')) if contributors_output else 0

    # Get date range
    first_date = run_command('git log --reverse --pretty=format:"%ad" --date=short', cwd=project_dir)
    last_date = run_command('git log --pretty=format:"%ad" --date=short', cwd=project_dir)

    if first_date and last_date:
        info['first_date'] = first_date.split('\n')[0]
        info['last_date'] = last_date.split('\n')[0]
    else:
        info['first_date'] = 'unknown'
        info['last_date'] = 'unknown'

    return info


def calculate_snapshot_points(project_dir, total_commits):
    """Calculate commit hashes for snapshot points"""
    # Calculate positions
    snapshot1_num = max(5, total_commits * 20 // 100)
    snapshot2_num = total_commits * 60 // 100
    snapshot3_num = total_commits * 85 // 100

    # Get all commits
    commits_output = run_command('git log --reverse --oneline', cwd=project_dir)
    if not commits_output:
        return []

    commit_lines = commits_output.split('\n')

    snapshots = []
    for i, (num, percentage, stage) in enumerate([
        (snapshot1_num, 20, 'foundation'),
        (snapshot2_num, 60, 'growth'),
        (snapshot3_num, 85, 'mature')
    ], 1):
        if num < len(commit_lines):
            commit_line = commit_lines[num]
            commit_hash = commit_line.split()[0]

            snapshots.append({
                'number': i,
                'percentage': percentage,
                'commit_num': num,
                'commit_hash': commit_hash,
                'commit_line': commit_line,
                'stage': stage,
                'snapshot_name': f'code-collab-proj-v{i}-{stage}'
            })

    return snapshots


def confirm_proceed(message):
    """Ask user for confirmation"""
    response = input(f"{message} (Y/n): ").strip().lower()
    return response != 'n'


def run_create_snapshot(script_path, project_dir, commit_hash, snapshot_name):
    """Run the create_snapshot.py script"""
    cmd = [
        'python',
        str(script_path),
        str(project_dir),
        commit_hash,
        snapshot_name
    ]

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python create_all_snapshots.py <project_dir>")
        print()
        print("Example:")
        print("  python create_all_snapshots.py demo-project-full")
        print()
        print("This will create 3 snapshots:")
        print("  - code-collab-proj-v1-foundation (at ~20% of commits)")
        print("  - code-collab-proj-v2-growth (at ~60% of commits)")
        print("  - code-collab-proj-v3-mature (at ~85% of commits)")
        sys.exit(1)

    project_dir = Path(sys.argv[1])

    # Validate project directory
    if not project_dir.exists():
        print(f"Error: Project directory '{project_dir}' does not exist")
        sys.exit(1)

    if not (project_dir / '.git').exists():
        print(f"Error: '{project_dir}' is not a git repository")
        sys.exit(1)

    print("=" * 60)
    print("Creating Test Data Snapshots")
    print("=" * 60)
    print()
    print(f"Project: {project_dir}")
    print()

    # Get project info
    info = get_project_info(project_dir)

    print("Repository Info:")
    print(f"  Name: {info['name']}")
    print(f"  URL: {info['url']}")
    print(f"  Total Commits: {info['total_commits']}")
    print(f"  Contributors: {info['contributors']}")
    print(f"  Date Range: {info['first_date']} to {info['last_date']}")
    print()

    # Check if suitable
    if info['total_commits'] < 30:
        print("⚠️  Warning: This project has fewer than 30 commits.")
        print("   Snapshots may not show significant differences.")
        print()
        if not confirm_proceed("Continue anyway?"):
            print("Aborted.")
            sys.exit(0)

    # Calculate snapshot points
    print("Calculating snapshot points...")
    snapshots = calculate_snapshot_points(project_dir, info['total_commits'])

    if not snapshots:
        print("Error: Could not calculate snapshot points")
        sys.exit(1)

    print()
    print("Snapshot Points Selected:")
    for snap in snapshots:
        print(f"  {snap['number']}. {snap['stage'].capitalize()} (~{snap['percentage']}%, commit #{snap['commit_num']}): {snap['commit_line']}")
    print()

    if not confirm_proceed("Proceed with these snapshot points?"):
        print("Aborted. You can manually specify commits with create_snapshot.py")
        sys.exit(0)

    print()
    print("=" * 60)
    print("Creating Snapshots")
    print("=" * 60)
    print()

    # Get script path
    script_dir = Path(__file__).parent
    create_snapshot_script = script_dir / 'create_snapshot.py'

    if not create_snapshot_script.exists():
        print(f"Error: create_snapshot.py not found at {create_snapshot_script}")
        sys.exit(1)

    # Create each snapshot
    created_snapshots = []

    for snap in snapshots:
        print()
        print("─" * 60)
        print(f"Creating Snapshot {snap['number']}: {snap['stage'].capitalize()}")
        print("─" * 60)

        success = run_create_snapshot(
            create_snapshot_script,
            project_dir,
            snap['commit_hash'],
            snap['snapshot_name']
        )

        if success:
            created_snapshots.append(snap)
        else:
            print(f"Failed to create snapshot {snap['number']}")
            sys.exit(1)

    # Success summary
    print()
    print("=" * 60)
    print("✓✓✓ All Snapshots Created Successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print("1. Update snapshots.json with project information:")
    print("   Edit: backend/test-data/code-collab-proj-snapshots/snapshots.json")
    print()
    print("   Add these commit details:")
    for snap in created_snapshots:
        print(f"   - v{snap['number']} ({snap['stage']}): commit {snap['commit_hash']}")
    print()
    print("2. Verify the snapshots:")
    print("   cd backend/test-data/code-collab-proj-snapshots")
    print("   ls -lh *.zip")
    print()
    print("3. Test with the API:")
    print("   # Start backend server")
    print("   cd backend && python -m uvicorn src.api.main:app --reload")
    print()
    print("   # Upload snapshot 1")
    print("   curl -X POST http://localhost:8000/api/projects/analyze/upload \\")
    print("     -F \"file=@backend/test-data/code-collab-proj-snapshots/code-collab-proj-v1-foundation.zip\" \\")
    print("     | jq")
    print()
    print("4. Compare results between snapshots to verify progression is visible")
    print()
    print("Snapshot files created:")
    for snap in created_snapshots:
        print(f"  - {snap['snapshot_name']}.zip (commit: {snap['commit_hash']})")
    print()


if __name__ == '__main__':
    main()
