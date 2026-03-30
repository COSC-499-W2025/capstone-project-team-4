"""Service for listing projects by contributor GitHub username."""

import logging
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.models.schemas.contributor import (
    ContributorIdentityMatchSchema,
    ContributorProjectLinesSchema,
    ContributorProjectsByUsernameResponseSchema,
    ContributorActivityDaySchema,
    ContributorProjectHeatmapResponseSchema,
)
from src.repositories.contributor_repository import ContributorRepository
from src.utils.contributor_dedup import identity_matches, normalize_identity

logger = logging.getLogger(__name__)


class ContributorProjectsService:
    """Service for contributor project listings."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.contributor_repo = ContributorRepository(db)

    def list_projects_by_github_username(
        self, github_username: str
    ) -> ContributorProjectsByUsernameResponseSchema:
        """Return projects sorted by lines changed for a GitHub username."""
        username = github_username.strip()
        if not username:
            raise HTTPException(status_code=400, detail="GitHub username is required")

        records = self.contributor_repo.get_all_with_projects()

        normalized = normalize_identity(username)
        matched: List[tuple] = []
        for contributor, project in records:
            if identity_matches(
                normalized,
                name=contributor.name,
                email=contributor.email,
                github_username=contributor.github_username,
                github_email=contributor.github_email,
            ):
                matched.append((contributor, project))

        if not matched:
            raise HTTPException(
                status_code=404,
                detail=f"No contributor records found for {github_username}",
            )

        aggregated: dict[int, dict] = {}

        for contributor, project in matched:
            entry = aggregated.setdefault(
                project.id,
                {
                    "project": project,
                    "contributor_ids": set(),
                    "commits": 0,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "names": set(),
                    "emails": set(),
                    "github_usernames": set(),
                    "github_emails": set(),
                },
            )

            entry["contributor_ids"].add(contributor.id)
            entry["commits"] += contributor.commits or 0
            entry["lines_added"] += contributor.total_lines_added or 0
            entry["lines_deleted"] += contributor.total_lines_deleted or 0

            if contributor.name:
                entry["names"].add(contributor.name)
            if contributor.email:
                entry["emails"].add(contributor.email)
            if contributor.github_username:
                entry["github_usernames"].add(contributor.github_username)
            if contributor.github_email:
                entry["github_emails"].add(contributor.github_email)

        projects: List[ContributorProjectLinesSchema] = []
        for entry in aggregated.values():
            lines_changed = entry["lines_added"] + entry["lines_deleted"]
            contributor_ids = sorted(entry["contributor_ids"])
            projects.append(
                ContributorProjectLinesSchema(
                    project_id=entry["project"].id,
                    project_name=entry["project"].name,
                    contributor_id=contributor_ids[0],
                    contributor_ids=contributor_ids,
                    commits=entry["commits"],
                    total_lines_added=entry["lines_added"],
                    total_lines_deleted=entry["lines_deleted"],
                    total_lines_changed=lines_changed,
                    matched_identities=ContributorIdentityMatchSchema(
                        names=sorted(entry["names"]),
                        emails=sorted(entry["emails"]),
                        github_usernames=sorted(entry["github_usernames"]),
                        github_emails=sorted(entry["github_emails"]),
                    ),
                )
            )

        projects.sort(key=lambda item: item.total_lines_changed, reverse=True)

        return ContributorProjectsByUsernameResponseSchema(
            github_username=github_username,
            total_projects=len(projects),
            projects=projects,
        )

    def get_project_activity_heatmap(
        self, github_username: str, project_id: int
    ) -> ContributorProjectHeatmapResponseSchema:
        """Return commit counts grouped by day for a contributor identity within one project."""
        username = github_username.strip()
        if not username:
            raise HTTPException(status_code=400, detail="GitHub username is required")

        records = self.contributor_repo.get_all_with_projects()

        normalized = normalize_identity(username)
        matched_contributor_ids: set[int] = set()

        for contributor, project in records:
            if project.id != project_id:
                continue

            if identity_matches(
                normalized,
                name=contributor.name,
                email=contributor.email,
                github_username=contributor.github_username,
                github_email=contributor.github_email,
            ):
                matched_contributor_ids.add(contributor.id)

        if not matched_contributor_ids:
            raise HTTPException(
                status_code=404,
                detail=f"No contributor activity found for {github_username} in project {project_id}",
            )

        rows = self.contributor_repo.get_commit_counts_by_day_for_contributors(
            contributor_ids=list(matched_contributor_ids)
        )

        data = [
            ContributorActivityDaySchema(date=commit_date, count=count)
            for commit_date, count in rows
        ]

        return ContributorProjectHeatmapResponseSchema(
            project_id=project_id,
            data=data,
        )
