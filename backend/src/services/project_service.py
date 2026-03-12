"""Project service for project operations."""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import yaml
from src.core.detectors.language import EXTENSION_MAP
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.schemas.project import (
    ProjectSummary,
    ProjectList,
    ProjectDetail,
    ProjectThumbnailResponse,
)
from src.models.schemas.analysis import (
    AnalysisResult,
    AnalysisStatus,
    ComplexitySummary,
    TextualProjectShowcaseResponse,
)
from src.models.schemas.contributor import (
    ContributorAnalysisSchema,
    ProjectContributorsAnalysisResponse,
    ChangeStatsSchema,
)
from src.repositories.project_repository import ProjectRepository
from src.repositories.file_repository import FileRepository
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.repositories.skill_repository import SkillRepository
from src.models.orm.project_thumbnail import ProjectThumbnail

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: Session):
        """Initialize project service with database session."""
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.file_repo = FileRepository(db)
        self.contributor_repo = ContributorRepository(db)
        self.complexity_repo = ComplexityRepository(db)
        self.skill_repo = SkillRepository(db)

    @staticmethod
    def _get_domain_mapping_path() -> Path:
        """Return path to domain mapping config file."""
        return Path(__file__).resolve().parent.parent / "config" / "domain_mapping.yaml"

    @staticmethod
    def _load_domain_mapping() -> Dict[str, dict]:
        """Load domain mapping from config (cached in process)."""
        path = ProjectService._get_domain_mapping_path()
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    return data
        except FileNotFoundError:
            logger.warning("Domain mapping config not found at %s", path)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to load domain mapping: %s", exc)
        return {}

    @staticmethod
    def _build_domain_index(mapping: Dict[str, dict]) -> Dict[str, dict]:
        """Build reverse index for fast domain lookup."""
        paths: List[Tuple[str, str]] = []
        ext_map: Dict[str, str] = {}
        lang_map: Dict[str, str] = {}
        framework_map: Dict[str, str] = {}

        for domain, rule in mapping.items():
            for p in rule.get("paths", []) or []:
                paths.append((p.lower(), domain))
            for ext in rule.get("extensions", []) or []:
                ext_map[ext.lower()] = domain
            for lang in rule.get("languages", []) or []:
                lang_map[lang.lower()] = domain
            for fw in rule.get("frameworks", []) or []:
                framework_map[fw.lower()] = domain

        # Sort paths by length descending so deeper prefixes match first
        paths.sort(key=lambda item: len(item[0]), reverse=True)

        return {
            "paths": paths,
            "extensions": ext_map,
            "languages": lang_map,
            "frameworks": framework_map,
        }

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize paths for consistent matching."""
        if not path:
            return ""
        return path.replace("\\", "/").lstrip("./").lstrip("/").lower()

    @staticmethod
    def _classify_domain(
        path: str,
        language: Optional[str],
        domain_index: Dict[str, dict],
    ) -> Optional[str]:
        """Determine domain for a file using language only (paths/extensions ignored)."""
        if language:
            lang_key = language.lower()
            if lang_key in domain_index["languages"]:
                return domain_index["languages"][lang_key]
        return None

    def list_projects(self, page: int = 1, page_size: int = 20) -> ProjectList:
        skip = (page - 1) * page_size
        total = self.project_repo.count()
        pages = (total + page_size - 1) // page_size

        summaries = self.project_repo.get_all_summaries(skip=skip, limit=page_size)

        # Populate thumbnail fields (feedback #4 / #9)
        project_ids = [s["id"] for s in summaries if s]
        thumb_map: dict[int, datetime] = {}

        if project_ids:
            rows = self.db.execute(
                select(ProjectThumbnail.project_id, ProjectThumbnail.updated_at).where(
                    ProjectThumbnail.project_id.in_(project_ids)
                )
            ).all()
            thumb_map = {pid: updated_at for pid, updated_at in rows}

        items: list[ProjectSummary] = []
        for s in summaries:
            if not s:
                continue

            thumb_updated_at = thumb_map.get(s["id"])
            has_thumb = thumb_updated_at is not None

            items.append(
                ProjectSummary(
                    id=s["id"],
                    name=s["name"],
                    source_type=s["source_type"],
                    created_at=s["created_at"],
                    zip_uploaded_at=s.get("zip_uploaded_at"),
                    first_file_created=s.get("first_file_created"),
                    first_commit_date=s.get("first_commit_date"),
                    project_started_at=s.get("project_started_at"),
                    file_count=s["file_count"],
                    language_count=s["language_count"],
                    framework_count=s["framework_count"],
                    library_count=s["library_count"],
                    tool_count=s["tool_count"],
                    contributor_count=s["contributor_count"],
                    skill_count=s["skill_count"],
                    has_thumbnail=has_thumb,
                    thumbnail_updated_at=thumb_updated_at,
                    thumbnail_endpoint=None,  # filled at route level via url_for
                )
            )

        return ProjectList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_project_detail(self, project_id: int) -> Optional[ProjectDetail]:
        """Get project detail (used by GET /projects/{id}) including thumbnail metadata."""
        project = self.project_repo.get(project_id)
        if not project:
            return None

        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        libraries = self.project_repo.get_libraries(project_id)
        tools = self.project_repo.get_tools(project_id)
        total_loc = self.project_repo.get_total_lines_of_code(project_id)
        complexity_summary = self.complexity_repo.get_summary(project_id)

        summary = self.project_repo.get_summary(project_id) or {}

        thumb = self.db.get(ProjectThumbnail, project_id)
        has_thumb = thumb is not None
        thumb_updated_at = thumb.updated_at if thumb else None

        return ProjectDetail(
            id=project.id,
            name=project.name,
            source_type=project.source_type,
            created_at=project.created_at,
            updated_at=project.updated_at,
            root_path=project.root_path,
            source_url=project.source_url,
            zip_uploaded_at=project.zip_uploaded_at,
            first_file_created=project.first_file_created,
            first_commit_date=project.first_commit_date,
            project_started_at=project.project_started_at,
            file_count=summary.get("file_count", 0),
            contributor_count=summary.get("contributor_count", 0),
            skill_count=summary.get("skill_count", 0),
            framework_count=summary.get("framework_count", 0),
            language_count=summary.get("language_count", 0),
            library_count=summary.get("library_count", 0),
            tool_count=summary.get("tool_count", 0),
            languages=languages,
            frameworks=frameworks,
            libraries=libraries,
            tools=tools,
            total_lines_of_code=total_loc,
            avg_complexity=complexity_summary.get("avg_complexity", 0.0),
            max_complexity=complexity_summary.get("max_complexity", 0),
            has_thumbnail=has_thumb,
            thumbnail_updated_at=thumb_updated_at,
            thumbnail_endpoint=None,  # set in route via url_for
        )

    def get_project(self, project_id: int) -> Optional[AnalysisResult]:
        """
        Get detailed project information.

        Args:
            project_id: ID of the project

        Returns:
            AnalysisResult or None if not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        # Get related data
        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        libraries = self.project_repo.get_libraries(project_id)
        tools = self.project_repo.get_tools(project_id)
        total_loc = self.project_repo.get_total_lines_of_code(project_id)
        complexity_summary = self.complexity_repo.get_summary(project_id)
        skills = self.skill_repo.get_by_project(project_id)

        # Get counts
        summary = self.project_repo.get_summary(project_id)

        @staticmethod
        def _to_str_list(items):
            if not items:
                return []
            out = []
            for x in items:
                if hasattr(x, "name") and getattr(x, "name") is not None:
                    out.append(str(getattr(x, "name")))
                elif isinstance(x, dict) and x.get("name") is not None:
                    out.append(str(x["name"]))
                else:
                    out.append(str(x))
            return out

        return AnalysisResult(
            project_id=project.id,
            project_name=project.name,
            status=AnalysisStatus.COMPLETED,
            source_type=project.source_type,
            source_url=project.source_url,
            created_at=project.created_at,
            updated_at=project.updated_at,
            zip_uploaded_at=project.zip_uploaded_at,
            first_file_created=project.first_file_created,
            first_commit_date=project.first_commit_date,
            project_started_at=project.project_started_at,
            file_count=summary["file_count"] if summary else 0,
            contributor_count=summary["contributor_count"] if summary else 0,
            skill_count=summary["skill_count"] if summary else 0,
            library_count=len(libraries),
            tool_count=len(tools),
            total_lines_of_code=total_loc,
            languages=_to_str_list(languages),
            frameworks=_to_str_list(frameworks),
            libraries=_to_str_list(libraries),
            tools_and_technologies=_to_str_list(tools),
            contextual_skills=_to_str_list(skills),
            complexity_summary=ComplexitySummary(
                total_functions=complexity_summary.get("total_functions", 0),
                avg_complexity=complexity_summary.get("avg_complexity", 0.0),
                max_complexity=complexity_summary.get("max_complexity", 0),
                high_complexity_count=complexity_summary.get(
                    "high_complexity_count", 0
                ),
            ),
        )

    def get_project_by_name(self, name: str) -> Optional[AnalysisResult]:
        """
        Get project by name.

        Args:
            name: Name of the project

        Returns:
            AnalysisResult or None if not found
        """
        project = self.project_repo.get_by_name(name)
        if not project:
            return None
        return self.get_project(project.id)

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project and all associated data.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if deleted, False if not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return False

        logger.info(f"Deleting project {project_id}: {project.name}")
        return self.project_repo.delete(project_id)

    def set_thumbnail(
        self,
        project_id: int,
        *,
        content_type: str,
        bytes_data: bytes,
        etag: Optional[str],
        thumbnail_endpoint: str,
        size_bytes: Optional[int] = None,
    ) -> Optional[ProjectThumbnailResponse]:
        """Create or replace a project's thumbnail in the DB."""
        project = self.project_repo.get(project_id)
        if not project:
            return None

        # Compute internally to avoid caller inconsistency (feedback #2)
        computed_size = len(bytes_data)
        size_bytes = computed_size
        thumb = self.db.get(ProjectThumbnail, project_id)
        now = datetime.utcnow()

        if thumb is None:
            thumb = ProjectThumbnail(
                project_id=project_id,
                image_bytes=bytes_data,
                content_type=content_type,
                size_bytes=size_bytes,
                etag=etag,
                updated_at=now,
            )
            self.db.add(thumb)
        else:
            thumb.image_bytes = bytes_data
            thumb.content_type = content_type
            thumb.size_bytes = size_bytes
            thumb.etag = etag
            thumb.updated_at = now

        self.db.commit()
        self.db.refresh(thumb)

        return ProjectThumbnailResponse(
            project_id=project_id,
            has_thumbnail=True,
            thumbnail_updated_at=thumb.updated_at,
            thumbnail_endpoint=thumbnail_endpoint,
            content_type=thumb.content_type,
            size_bytes=thumb.size_bytes,
            etag=thumb.etag,
        )

    def get_thumbnail(
        self, project_id: int
    ) -> Optional[Tuple[bytes, str, Optional[str]]]:
        """Return (bytes, content_type, etag) for a project's thumbnail, or None if missing."""
        thumb = self.db.get(ProjectThumbnail, project_id)
        if thumb is None:
            return None
        return (thumb.image_bytes, thumb.content_type, thumb.etag)

    def delete_thumbnail(self, project_id: int) -> bool:
        """Delete a project's thumbnail. Returns True if deleted, False if not found."""
        thumb = self.db.get(ProjectThumbnail, project_id)
        if thumb is None:
            return False
        self.db.delete(thumb)
        self.db.commit()
        return True

    def get_contributor_analysis(
        self, project_id: int
    ) -> Optional[ProjectContributorsAnalysisResponse]:
        """
        Get contributor analysis with contribution scores for a project.

        Calculates contribution score for each contributor using:
        - commits_percent (weight: 0.40)
        - lines_changed_percent (weight: 0.40)
        - files_touched_percent (weight: 0.20)

        Args:
            project_id: ID of the project

        Returns:
            ProjectContributorsAnalysisResponse with contribution analysis, or None if project not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        contributors = self.contributor_repo.get_by_project(project_id)
        if not contributors:
            return ProjectContributorsAnalysisResponse(
                project_id=project_id,
                project_name=project.name,
                total_contributors=0,
                contributors=[],
            )

        domain_mapping = self._load_domain_mapping()
        domain_index = self._build_domain_index(domain_mapping)

        files = self.file_repo.get_by_project(project_id, limit=100000)
        file_lang_map: Dict[str, Optional[str]] = {}
        for f in files:
            normalized = self._normalize_path(f.path)
            file_lang_map[normalized] = f.language.name if f.language else None

        # Calculate totals
        total_commits = sum(c.commits for c in contributors)
        total_lines_added = sum(c.total_lines_added for c in contributors)
        total_lines_deleted = sum(c.total_lines_deleted for c in contributors)
        total_lines_changed = total_lines_added + total_lines_deleted
        total_files = sum(len(c.files_modified) for c in contributors)

        # First pass: calculate contribution scores for all contributors
        scores_and_data = []
        for c in contributors:
            # Calculate normalized values (0.0 - 1.0)
            commits_norm = c.commits / total_commits if total_commits > 0 else 0.0
            lines_norm = (
                (c.total_lines_added + c.total_lines_deleted) / total_lines_changed
                if total_lines_changed > 0
                else 0.0
            )
            files_norm = len(c.files_modified) / total_files if total_files > 0 else 0.0

            # Apply weights (4:4:2 ratio)
            weighted_score = (
                (commits_norm * 0.40) + (lines_norm * 0.40) + (files_norm * 0.20)
            )
            contribution_score = round(weighted_score * 100, 2)

            # Calculate net lines
            net_lines = c.total_lines_added - c.total_lines_deleted

            # Calculate change statistics
            contributor_total_lines_changed = (
                c.total_lines_added + c.total_lines_deleted
            )
            lines_changed_per_commit = (
                round(contributor_total_lines_changed / c.commits, 2)
                if c.commits > 0
                else 0.0
            )
            files_changed = len(c.files_modified)

            domain_counts: Dict[str, int] = defaultdict(int)
            debug_files = []
            for fm in c.files_modified:
                filename = fm.filename or ""
                # Skip .json files
                if filename.endswith(".json"):
                    continue
                weight = fm.modifications or 1
                normalized = self._normalize_path(filename)
                language = file_lang_map.get(normalized)
                if not language:
                    # Fallback: infer language from file extension when not stored
                    language = EXTENSION_MAP.get(Path(filename).suffix.lower())
                domain = self._classify_domain(filename, language, domain_index)
                if not domain:
                    debug_files.append((filename, language, "NO_DOMAIN"))
                    continue
                domain_counts[domain] += weight
                debug_files.append((filename, language, domain))

            logger.debug(
                f"Contributor {c.name}: domain_counts={dict(domain_counts)}, sample_files={debug_files[:3]}"
            )
            domain_total = sum(domain_counts.values())
            area_scores = {}
            if domain_total > 0:
                for domain, count in domain_counts.items():
                    area_scores[domain] = round((count / domain_total) * 100, 2)

            scores_and_data.append(
                {
                    "contributor": c,
                    "contribution_score": contribution_score,
                    "net_lines": net_lines,
                    "files_touched": len(c.files_modified),
                    "total_lines_changed": contributor_total_lines_changed,
                    "lines_changed_per_commit": lines_changed_per_commit,
                    "files_changed": files_changed,
                }
            )

        # Calculate total score for percentage calculation
        total_score = sum(item["contribution_score"] for item in scores_and_data)

        # Second pass: build analysis schema with percentages
        analysis_list = []
        for item in scores_and_data:
            contribution_percentage = (
                round((item["contribution_score"] / total_score) * 100, 2)
                if total_score > 0
                else 0.0
            )

            changes = ChangeStatsSchema(
                total_lines_added=item["contributor"].total_lines_added,
                total_lines_deleted=item["contributor"].total_lines_deleted,
                total_lines_changed=item["total_lines_changed"],
                lines_changed_per_commit=item["lines_changed_per_commit"],
                files_changed=item["files_changed"],
            )

            analysis_list.append(
                ContributorAnalysisSchema(
                    id=item["contributor"].id,
                    name=item["contributor"].name,
                    email=item["contributor"].email,
                    commits=item["contributor"].commits,
                    total_lines_added=item["contributor"].total_lines_added,
                    total_lines_deleted=item["contributor"].total_lines_deleted,
                    net_lines=item["net_lines"],
                    files_touched=item["files_touched"],
                    contribution_score=item["contribution_score"],
                    contribution_percentage=contribution_percentage,
                    changes=changes,
                    area_scores=area_scores,
                    top_paths=[],
                    top_frameworks=[],
                )
            )

        return ProjectContributorsAnalysisResponse(
            project_id=project_id,
            project_name=project.name,
            total_contributors=len(contributors),
            contributors=analysis_list,
        )

    def project_exists(self, project_id: int) -> bool:
        """Check if a project exists."""
        return self.project_repo.get(project_id) is not None

    def get_textual_project_showcase(
        self, project_id: int
    ) -> Optional[TextualProjectShowcaseResponse]:
        """Return the portfolio-ready textual showcase for a project."""
        analysis = self.get_project(project_id)
        if analysis is None:
            return None

        return TextualProjectShowcaseResponse(
            **analysis.model_dump(),
            short_description=None,
        )
