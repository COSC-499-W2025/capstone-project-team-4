import unittest
from unittest.mock import patch, MagicMock

from src.core.github_api_extraction import (
    extract_skills,
    _ext_of,
    _get_paginated,
    get_language_line_counts,
    get_repo_data,
    get_objective_contributions,
    get_skill_growth,
    get_team_culture,
)


class TestSkillExtractor(unittest.TestCase):
    # ---------------- Skills ----------------
    def test_extract_skills(self):
        text = "This project uses Python, Flask, pandas and Docker."
        expected = ["docker", "flask", "pandas", "python"]
        self.assertEqual(extract_skills(text), expected)

    def test_extract_skills_empty(self):
        self.assertEqual(extract_skills(""), [])

    # ---------------- _ext_of ----------------
    def test__ext_of(self):
        self.assertEqual(_ext_of("test.py"), ".py")
        self.assertEqual(_ext_of("README"), "")
        self.assertEqual(_ext_of("index.html"), ".html")

    # ---------------- _get_paginated ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test__get_paginated(self, mock_get):
        # 2 pages then empty
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: [{"x": 1}, {"x": 2}]),
            MagicMock(status_code=200, json=lambda: [{"x": 3}]),
            MagicMock(status_code=200, json=lambda: []),
        ]
        items = list(_get_paginated("https://api.example.com/items"))
        self.assertEqual(items, [{"x": 1}, {"x": 2}, {"x": 3}])

    # ---------------- get_language_line_counts ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_language_line_counts(self, mock_get):
        """
        Ensure line counts are computed correctly and that mocking requests.get
        does not cause MagicMock arithmetic on .text.
        """
        from src.core.github_api_extraction import get_language_line_counts, _list_contents

        # Fake "response" object for file downloads with real .text
        class FakeResp:
            def __init__(self, text):
                self.status_code = 200
                self.text = text

        # First call: _list_contents -> JSON listing
        # Next calls: two file downloads (Python + JS)
        file_list = [
            {
                "name": "a.py",
                "path": "a.py",
                "type": "file",
                "download_url": "url1",
                "size": 10,
            },
            {
                "name": "b.js",
                "path": "b.js",
                "type": "file",
                "download_url": "url2",
                "size": 10,
            },
        ]

        mock_get.side_effect = [
            # _list_contents call
            MagicMock(status_code=200, json=lambda: file_list),
            # download a.py  (2 lines)
            FakeResp("print('x')\nprint('y')\n"),
            # download b.js  (1 line)
            FakeResp("console.log('x')\n"),
        ]

        counts = get_language_line_counts("o", "r", "main")
        self.assertEqual(counts["Python"], 2)
        self.assertEqual(counts["JavaScript"], 1)

    # ---------------- get_repo_data ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_repo_data(self, mock_get):
        """
        Test that get_repo_data returns info, langs and decoded README.
        """
        from src.core.github_api_extraction import get_repo_data

        mock_get.side_effect = [
            # repo info
            MagicMock(status_code=200, json=lambda: {"default_branch": "main"}),
            # languages
            MagicMock(status_code=200, json=lambda: {"Python": 1234}),
            # README (base64 for "Hello README")
            MagicMock(
                status_code=200,
                json=lambda: {
                    "content": "SGVsbG8gUkVBRE1F",  # "Hello README"
                },
            ),
        ]

        info, langs, readme_text = get_repo_data("owner", "repo", ref="dev")
        self.assertEqual(info["default_branch"], "main")
        self.assertEqual(langs["Python"], 1234)
        self.assertIn("Hello README", readme_text)

    # ---------------- get_objective_contributions ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_objective_contributions(self, mock_get):
        """
        Test stats aggregation: commits, additions, deletions, files.
        """
        # 1) _get_paginated for commits (2 commits), then empty
        # 2) commit detail for sha "abc"
        # 3) commit detail for sha "def"
        mock_get.side_effect = [
            # commits page1
            MagicMock(
                status_code=200,
                json=lambda: [
                    {
                        "sha": "abc",
                        "author": {"login": "user1"},
                        "commit": {"author": {"date": "2024-01-01T00:00:00Z"}},
                    },
                    {
                        "sha": "def",
                        "author": {"login": "user2"},
                        "commit": {"author": {"date": "2024-01-02T00:00:00Z"}},
                    },
                ],
            ),
            # commits page2 -> stop
            MagicMock(status_code=200, json=lambda: []),
            # detail for abc
            MagicMock(
                status_code=200,
                json=lambda: {
                    "stats": {"additions": 10, "deletions": 2},
                    "files": [{"filename": "file1.py"}],
                },
            ),
            # detail for def
            MagicMock(
                status_code=200,
                json=lambda: {
                    "stats": {"additions": 4, "deletions": 1},
                    "files": [{"filename": "file2.js"}],
                },
            ),
        ]

        stats = get_objective_contributions("owner", "repo", max_commits=10)
        self.assertIn("user1", stats)
        self.assertIn("user2", stats)
        self.assertEqual(stats["user1"]["commits"], 1)
        self.assertEqual(stats["user1"]["add"], 10)
        self.assertEqual(stats["user1"]["del"], 2)
        self.assertEqual(stats["user1"]["files"], 1)
        self.assertEqual(stats["user2"]["add"], 4)
        self.assertEqual(stats["user2"]["del"], 1)

    # ---------------- get_skill_growth ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_skill_growth(self, mock_get):
        """
        Test that get_skill_growth builds a timeline and accumulates skills.
        """
        from src.core.github_api_extraction import EXT_SKILL_MAP

        # commits page1: 2 commits
        mock_get.side_effect = [
            # _get_paginated → commits
            MagicMock(
                status_code=200,
                json=lambda: [
                    {
                        "sha": "1",
                        "author": {"login": "dev1"},
                        "commit": {"author": {"date": "2020-01-01T00:00:00Z"}},
                    },
                    {
                        "sha": "2",
                        "author": {"login": "dev1"},
                        "commit": {"author": {"date": "2020-01-02T00:00:00Z"}},
                    },
                ],
            ),
            # page2 -> stop
            MagicMock(status_code=200, json=lambda: []),
            # detail for sha "1": Python file
            MagicMock(
                status_code=200,
                json=lambda: {
                    "files": [{"filename": "main.py"}],
                },
            ),
            # detail for sha "2": SQL file + test file
            MagicMock(
                status_code=200,
                json=lambda: {
                    "files": [{"filename": "schema.sql"}, {"filename": "test_main.py"}],
                },
            ),
        ]

        timeline = get_skill_growth("owner", "repo", max_commits=10)
        self.assertIn("dev1", timeline)
        dev_timeline = timeline["dev1"]
        # should have 2 entries
        self.assertEqual(len(dev_timeline), 2)
        # final skills should include Python, SQL, Testing
        final_skills = dev_timeline[-1]["skills"]
        self.assertIn("Python", final_skills)
        self.assertIn("SQL", final_skills)
        self.assertIn("Testing", final_skills)

    # ---------------- get_team_culture ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_team_culture_no_merged(self, mock_get):
        """
        If there are PRs but none merged, median_merge_hours should be 0.
        """
        mock_get.side_effect = [
            # _get_paginated → PR list (page1)
            MagicMock(
                status_code=200,
                json=lambda: [
                    {
                        "number": 1,
                        "created_at": "2024-01-01T00:00:00Z",
                        "merged_at": None,
                    }
                ],
            ),
            # page2 -> stop
            MagicMock(status_code=200, json=lambda: []),
            # reviews for PR #1
            MagicMock(status_code=200, json=lambda: []),
            # comments for PR #1
            MagicMock(status_code=200, json=lambda: []),
        ]

        culture = get_team_culture("owner", "repo")
        self.assertEqual(culture["total_prs"], 1)
        self.assertEqual(culture["median_merge_hours"], 0)
        self.assertEqual(culture["avg_reviews"], 0)
        self.assertEqual(culture["avg_comments"], 0)

    @patch("src.core.github_api_extraction.requests.get")
    def test_get_team_culture_with_merged(self, mock_get):
        """
        At least one merged PR should produce a positive or zero median_merge_hours.
        """
        mock_get.side_effect = [
            # _get_paginated → PR list
            MagicMock(
                status_code=200,
                json=lambda: [
                    {
                        "number": 1,
                        "created_at": "2024-01-01T00:00:00Z",
                        "merged_at": "2024-01-02T00:00:00Z",
                    }
                ],
            ),
            # page2 -> stop
            MagicMock(status_code=200, json=lambda: []),
            # reviews for PR #1 (2 reviews)
            MagicMock(
                status_code=200,
                json=lambda: [
                    {"id": 101, "user": {"login": "rev1"}},
                    {"id": 102, "user": {"login": "rev2"}},
                ],
            ),
            # comments for PR #1 (1 comment)
            MagicMock(
                status_code=200,
                json=lambda: [
                    {"id": 201, "user": {"login": "c1"}},
                ],
            ),
        ]

        culture = get_team_culture("owner", "repo")
        self.assertEqual(culture["total_prs"], 1)
        # 24 hours between created and merged
        self.assertGreaterEqual(culture["median_merge_hours"], 24 - 0.001)
        self.assertEqual(culture["avg_reviews"], 2)
        self.assertEqual(culture["avg_comments"], 1)

    # ---------------- get_development_rhythm ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_development_rhythm(self, mock_get):
        from src.core.github_api_extraction import get_development_rhythm

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: [
                {
                    "sha": "1",
                    "author": {"login": "aaa"},
                    "commit": {"author": {"date": "2024-01-01T10:00:00Z"}},  # Tue 10AM UTC
                },
                {
                    "sha": "2",
                    "author": {"login": "aaa"},
                    "commit": {"author": {"date": "2024-01-02T22:00:00Z"}},  # Wed 10PM UTC
                }
            ]),
            MagicMock(status_code=200, json=lambda: []),  # stop pagination
        ]

        rhythm = get_development_rhythm("o", "r")
        self.assertIn("aaa", rhythm)
        self.assertEqual(rhythm["aaa"]["total"], 2)
        self.assertGreater(sum(rhythm["aaa"]["weekday"].values()), 0)
        self.assertGreater(sum(rhythm["aaa"]["hour"].values()), 0)

    # ---------------- get_technical_decisions ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_technical_decisions(self, mock_get):
        from src.core.github_api_extraction import get_technical_decisions

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: [
                {
                    "sha": "1",
                    "author": {"login": "dev"},
                    "commit": {"message": "fix memory leak"},
                },
                {
                    "sha": "2",
                    "author": {"login": "dev"},
                    "commit": {"message": "refactor module"},
                }
            ]),
            MagicMock(status_code=200, json=lambda: []),  # stop pagination
        ]

        td = get_technical_decisions("o", "r")
        self.assertIn("dev", td)
        self.assertGreater(td["dev"]["bugfix"], 0)
        self.assertGreater(td["dev"]["refactor"], 0)

    # ---------------- get_role_distribution ----------------
    @patch("src.core.github_api_extraction.requests.get")
    def test_get_role_distribution(self, mock_get):
        from src.core.github_api_extraction import get_role_distribution

        mock_get.side_effect = [
            # commits page
            MagicMock(status_code=200, json=lambda: [
                {"author": {"login": "alice"}},
                {"author": {"login": "bob"}},
            ]),
            MagicMock(status_code=200, json=lambda: []),  # stop commits pagination

            # PRs page
            MagicMock(status_code=200, json=lambda: [
                {"number": 7, "user": {"login": "alice"}},  # PR by alice
            ]),
            MagicMock(status_code=200, json=lambda: []),  # stop PR pagination

            # PR 7 → reviews (bob reviews)
            MagicMock(status_code=200, json=lambda: [
                {"user": {"login": "bob"}},
            ]),

            # PR 7 → comments (bob comments)
            MagicMock(status_code=200, json=lambda: [
                {"user": {"login": "bob"}},
            ]),
        ]

        roles = get_role_distribution("o", "r")
        self.assertEqual(roles["alice"]["commits"], 1)   # from commits
        self.assertEqual(roles["bob"]["commits"], 1)     # from commits
        self.assertEqual(roles["alice"]["opened_prs"], 1)
        self.assertEqual(roles["bob"]["reviews"], 1)
        self.assertEqual(roles["bob"]["comments"], 1)


if __name__ == "__main__":
    unittest.main()
