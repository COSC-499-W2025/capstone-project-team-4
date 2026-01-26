"""Contributors stats on default branch endpoint."""

import logging
import os
import subprocess
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.repositories.project_repository import ProjectRepository
from src.api.exceptions import ProjectNotFoundError
from src.api.routes.projects import _find_git_root
from src.utils.contributor_dedup import cluster_authors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}/contributors/default-branch-stats-same-as-github")
async def get_default_branch_stats(
    project_id: int,
    include_merges: bool = False,
    include_renames: bool = False,
    db: Session = Depends(get_db),
):
    """Return lines added/deleted per author on default branch only.

    - Targets default remote branch (origin/HEAD or origin/main/master)
    - Uses `git log origin/HEAD` with --use-mailmap, --no-merges (default), --no-renames (default)
    - Mirrors: git log "origin/$DEFAULT" --no-merges --no-renames --use-mailmap --numstat --pretty='%aN <%aE>'
    - Sorted by total_lines_changed descending
    """
    project_repo = ProjectRepository(db)
    project_orm = project_repo.get(project_id)
    if not project_orm:
        raise ProjectNotFoundError(project_id)

    root_path = project_orm.root_path
    git_root = _find_git_root(root_path) or _find_git_root(__file__)
    if not git_root:
        raise HTTPException(
            status_code=400,
            detail=f"Git repository not found for project root_path: {root_path}",
        )

    # Resolve default branch - check environment variable first, then origin/HEAD
    default_branch_env = os.environ.get("DEFAULT")
    
    if default_branch_env:
        default_branch_ref = f"origin/{default_branch_env}"
        # Verify branch exists
        cmd_test = ["git", "-C", git_root, "rev-parse", default_branch_ref]
        proc_test = subprocess.run(cmd_test, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc_test.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"DEFAULT branch 'origin/{default_branch_env}' not found.",
            )
    else:
        # Resolve default branch via origin/HEAD
        cmd_head = ["git", "-C", git_root, "symbolic-ref", "refs/remotes/origin/HEAD"]
        proc_head = subprocess.run(cmd_head, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if proc_head.returncode == 0:
            # Output format: "ref: refs/remotes/origin/main"
            ref_output = proc_head.stdout.strip()
            if ref_output.startswith("ref: "):
                default_branch_ref = ref_output[5:]  # e.g., "refs/remotes/origin/main"
            else:
                default_branch_ref = ref_output
        else:
            # Fallback to common default branch names
            for candidate in ["origin/main", "origin/master"]:
                cmd_test = ["git", "-C", git_root, "rev-parse", candidate]
                proc_test = subprocess.run(cmd_test, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc_test.returncode == 0:
                    default_branch_ref = candidate
                    break
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not determine default branch. DEFAULT env var, origin/HEAD, origin/main, or origin/master not found.",
                )

    cmd = [
        "git",
        "-C",
        git_root,
        "log",
        default_branch_ref,
        "--use-mailmap",
        "--numstat",
        "--pretty=%aN <%aE>",
    ]
    if not include_merges:
        cmd.insert(5, "--no-merges")
    if not include_renames:
        # Insert after --no-merges if present
        insert_pos = 6 if not include_merges else 5
        cmd.insert(insert_pos, "--no-renames")

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=proc.stderr.strip() or "git log failed")

    add_totals: dict[str, int] = {}
    del_totals: dict[str, int] = {}
    current_author = None

    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        # Author line
        if len(parts) == 1 and parts[0].strip():
            current_author = parts[0].strip()
            continue
        # Numstat line
        if len(parts) == 3 and current_author:
            ins, dele, _path = parts
            if ins == "-" or dele == "-":
                continue
            try:
                ins_i = int(ins)
                del_i = int(dele)
            except ValueError:
                continue
            add_totals[current_author] = add_totals.get(current_author, 0) + ins_i
            del_totals[current_author] = del_totals.get(current_author, 0) + del_i

    raw_stats = []
    for author, added in add_totals.items():
        deleted = del_totals.get(author, 0)
        raw_stats.append({"author": author, "added": added, "deleted": deleted})

    items = cluster_authors(raw_stats)

    items.sort(key=lambda x: x["total_lines_changed"], reverse=True)

    return {
        "project_id": project_id,
        "project_name": project_orm.name,
        "root_path": root_path,
        "git_root": git_root,
        "default_branch_ref": default_branch_ref,
        "include_merges": include_merges,
        "include_renames": include_renames,
        "total_contributors": len(items),
        "items": items,
    }
