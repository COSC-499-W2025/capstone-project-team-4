"""
Re-analyze a project to populate new contributor fields.

Usage:
    python utils/reanalyze_project.py <project_id>
    python utils/reanalyze_project.py 19
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.database import get_db_context
from src.repositories.project_repository import ProjectRepository
from src.repositories.contributor_repository import ContributorRepository
from src.core.analyzers.contributor import analyze_contributors


def reanalyze_project_contributors(project_id: int):
    """Re-analyze contributors for a project to populate new fields."""
    
    with get_db_context() as db:
        project_repo = ProjectRepository(db)
        contributor_repo = ContributorRepository(db)
        
        # Get project
        project = project_repo.get(project_id)
        if not project:
            print(f"✗ Project {project_id} not found")
            return False
        
        print(f"Re-analyzing project: {project.name} (ID: {project_id})")
        
        # Check if project has a file path
        if not project.file_path:
            print(f"✗ Project has no file path")
            return False
        
        project_path = Path(project.file_path)
        if not project_path.exists():
            print(f"✗ Project path does not exist: {project_path}")
            return False
        
        # Analyze contributors
        print("Analyzing contributors...")
        contributors = analyze_contributors(str(project_path), use_all_branches=True)
        
        if not contributors:
            print("✗ No contributors found")
            return False
        
        print(f"Found {len(contributors)} contributors")
        
        # Delete old contributor data
        print("Deleting old contributor data...")
        contributor_repo.delete_by_project_id(project_id)
        
        # Save new contributor data
        print("Saving new contributor data...")
        contributors_data = []
        for c in contributors:
            files_modified = []
            for filename, mods in c.get("files_modified", {}).items():
                files_modified.append({
                    "filename": filename,
                    "modifications": mods,
                })

            contributors_data.append({
                "project_id": project_id,
                "name": c.get("name"),
                "email": c.get("email"),
                "github_username": c.get("github_username"),
                "github_email": c.get("github_email"),
                "commits": c.get("commits", 0),
                "percent": c.get("percent", 0.0),
                "total_lines_added": c.get("total_lines_added", 0),
                "total_lines_deleted": c.get("total_lines_deleted", 0),
                "files_modified": files_modified,
            })
        
        contributor_repo.create_contributors_bulk(contributors_data)
        
        # Show results
        print("\n" + "=" * 80)
        print("Updated contributors:")
        print("=" * 80)
        
        for c in sorted(contributors_data, key=lambda x: x['commits'], reverse=True)[:5]:
            print(f"\n  {c['name']}")
            print(f"    email:           {c.get('email') or 'null'}")
            print(f"    github_username: {c.get('github_username') or 'null'}")
            print(f"    github_email:    {c.get('github_email') or 'null'}")
            print(f"    commits:         {c['commits']}")
        
        print("\n" + "=" * 80)
        print(f"✓ Successfully re-analyzed project {project_id}")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils/reanalyze_project.py <project_id>")
        print("Example: python utils/reanalyze_project.py 19")
        sys.exit(1)
    
    try:
        project_id = int(sys.argv[1])
        success = reanalyze_project_contributors(project_id)
        sys.exit(0 if success else 1)
    except ValueError:
        print("Error: Project ID must be a number")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
