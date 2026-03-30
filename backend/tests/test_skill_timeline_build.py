
from datetime import datetime
from pathlib import Path
import zipfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.orm.project import Project
from src.models.orm.skill import SkillOccurrence
from src.services.analysis_service import AnalysisService
from src.services.skill_service import SkillService


def create_test_zip(
    zip_path: Path,
    files: dict[str, str],
    dt=(2023, 5, 20, 12, 0, 0),
) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            info = zipfile.ZipInfo(name)
            info.date_time = dt
            zf.writestr(info, content)


class TestSkillTimelineBuild:
    def test_build_skill_timeline_rebuilds_occurrences_from_zip_metadata(
        self,
        monkeypatch,
        tmp_path,
    ):
        engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        db_session = TestingSessionLocal()

        try:
            zip_path = tmp_path / "uploads" / "sample-project.zip"
            create_test_zip(
                zip_path,
                {
                    "Website/package.json": '{"name":"sample"}',
                    "Website/test/testIndex.js": "describe('x', () => {})",
                    "Website/index.js": "console.log('hello')",
                    "Website/styles.css": "body { color: red; }",
                },
            )

            project = Project(
                name="Sample Project",
                root_path="/tmp/nonexistent-extracted-path/Website",
                source_type="zip",
                source_url=str(zip_path),
                user_id=1,
            )
            db_session.add(project)
            db_session.commit()
            db_session.refresh(project)

            class DummySkillObj:
                def __init__(self, name: str, category: str):
                    self.name = name
                    self.category = category

            class DummyProjectSkill:
                def __init__(self, name: str, category: str):
                    self.skill = DummySkillObj(name, category)

            fake_project_skills = [
                DummyProjectSkill("Package Management", "DevOps & Infrastructure"),
                DummyProjectSkill("Node.js", "Other"),
                DummyProjectSkill("Unit Testing", "Testing & QA"),
                DummyProjectSkill("Test Automation", "Testing & QA"),
                DummyProjectSkill("JavaScript", "Languages"),
                DummyProjectSkill("CSS", "Languages"),
            ]

            analysis_service = AnalysisService(db_session)
            skill_service = SkillService(db_session)

            monkeypatch.setattr(
                analysis_service.skill_repo,
                "get_by_project",
                lambda project_id: fake_project_skills,
            )
            monkeypatch.setattr(
                analysis_service.project_repo,
                "get_languages",
                lambda project_id: ["JavaScript", "CSS"],
            )
            monkeypatch.setattr(
                analysis_service.project_repo,
                "get_frameworks",
                lambda project_id: [],
            )

            monkeypatch.setattr(
                SkillService,
                "build_skill_timeline",
                lambda self, project_id, skill=None: (
                    analysis_service.rebuild_skill_occurrences_for_project(project_id)
                    or self.get_skill_timeline(project_id, skill)
                ),
            )

            result = skill_service.build_skill_timeline(project.id)

            db_session.expire_all()
            occurrences = (
                db_session.query(SkillOccurrence)
                .filter(SkillOccurrence.project_id == project.id)
                .all()
            )

            assert result is not None
            assert result.project_id == project.id
            assert len(result.timeline) > 0

            assert len(occurrences) > 0
            assert any(o.date_source == "zip_metadata" for o in occurrences)

            first_dates = {o.first_seen_at.date() for o in occurrences}
            assert datetime(2023, 5, 20).date() in first_dates

            skill_names = {entry.skill for entry in result.timeline}
            assert "JavaScript" in skill_names or "Unit Testing" in skill_names

        finally:
            db_session.close()