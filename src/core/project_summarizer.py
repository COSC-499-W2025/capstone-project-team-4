"""
Top Ranked Project Summarizer

This module provides comprehensive project analysis and ranking capabilities,
allowing users to identify their most significant projects based on various metrics.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal, Tuple
import sqlite3
import json
from datetime import datetime

from .database import get_connection


SortCriteria = Literal[
    "complexity", "contributions", "skills", "lines_of_code", 
    "file_count", "recent", "comprehensive"
]


@dataclass
class ProjectSummary:
    """Comprehensive summary of a project's characteristics."""
    project_id: int
    name: str
    path: str
    timestamp: str
    
    # Metrics
    total_files: int
    lines_of_code: int
    contributors_count: int
    skills_count: int
    complexity_score: float
    comprehensive_score: float
    
    # Detailed data
    contributors: List[Dict[str, Any]]
    top_skills: List[str]
    languages: List[str]
    frameworks: List[str]
    complexity_functions: List[Dict[str, Any]]
    
    # Resume item
    resume_title: str
    resume_highlights: List[str]


class ProjectSummarizer:
    """Analyzes and ranks projects from the database."""
    
    def __init__(self):
        self.conn = get_connection()
    
    def get_all_projects(self) -> List[ProjectSummary]:
        """Retrieve all projects with comprehensive analysis."""
        cur = self.conn.cursor()
        
        # Get basic project info
        cur.execute("""
            SELECT id, name, root, timestamp
            FROM projects
            ORDER BY timestamp DESC
        """)
        
        projects = []
        for row in cur.fetchall():
            project_id, name, path, timestamp = row
            summary = self._build_project_summary(project_id, name, path, timestamp)
            projects.append(summary)
        
        return projects
    
    def _build_project_summary(self, project_id: int, name: str, path: str, timestamp: str) -> ProjectSummary:
        """Build a comprehensive project summary."""
        cur = self.conn.cursor()
        
        # Get file count and total file size (as proxy for project size)
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(file_size), 0)
            FROM files 
            WHERE project_id = ?
        """, (project_id,))
        file_count, total_size = cur.fetchone()
        
        # Get contributors
        cur.execute("""
            SELECT name, email, commits, total_lines_added, total_lines_deleted, percent
            FROM contributors 
            WHERE project_id = ?
            ORDER BY commits DESC
        """, (project_id,))
        
        contributors = []
        for row in cur.fetchall():
            contributors.append({
                'name': row[0],
                'email': row[1],
                'commits': row[2],
                'total_lines_added': row[3],
                'total_lines_deleted': row[4],
                'percent': row[5],
                'files_touched': 0  # Not available in current schema
            })
        
        # Get complexity data
        cur.execute("""
            SELECT AVG(cyclomatic_complexity), COUNT(*), MAX(cyclomatic_complexity)
            FROM complexity 
            WHERE project_id = ?
        """, (project_id,))
        complexity_data = cur.fetchone()
        avg_complexity = complexity_data[0] or 0
        function_count = complexity_data[1] or 0
        max_complexity = complexity_data[2] or 0
        
        # Get top complex functions
        cur.execute("""
            SELECT file_path, function_name, cyclomatic_complexity, start_line, end_line
            FROM complexity 
            WHERE project_id = ?
            ORDER BY cyclomatic_complexity DESC
            LIMIT 5
        """, (project_id,))
        
        complexity_functions = []
        for row in cur.fetchall():
            complexity_functions.append({
                'file_path': row[0],
                'name': row[1],  # This is function_name from the query
                'complexity': row[2],
                'start_line': row[3],
                'end_line': row[4]
            })
        
        # Get skills from project_skills table
        cur.execute("""
            SELECT skill, category
            FROM project_skills
            WHERE project_id = ?
        """, (project_id,))
        
        skills_data = cur.fetchall()
        skills_dict = {}
        all_skills = []
        
        for skill, category in skills_data:
            if category not in skills_dict:
                skills_dict[category] = []
            skills_dict[category].append(skill)
            all_skills.append(skill)
        
        # Get resume item
        cur.execute("""
            SELECT title, highlights
            FROM resume_items
            WHERE project_id = ?
        """, (project_id,))
        
        resume_data = cur.fetchone()
        resume_title = resume_data[0] if resume_data else f"Project: {name}"
        resume_highlights = json.loads(resume_data[1]) if resume_data and resume_data[1] else []
        
        # Calculate comprehensive score
        complexity_score = avg_complexity * function_count + max_complexity * 0.5
        contribution_score = sum(c.get('commits', 0) for c in contributors)
        skills_score = len(all_skills) * 2
        size_score = (total_size / 1024) * 0.001  # Convert bytes to KB and scale
        
        comprehensive_score = (
            complexity_score * 0.3 +
            contribution_score * 0.3 +
            skills_score * 0.2 +
            size_score * 0.1 +
            file_count * 0.1
        )
        
        # Extract languages and frameworks from skills
        languages = skills_dict.get('Programming Languages', [])[:10]
        frameworks = skills_dict.get('Web Development', [])[:10]
        
        return ProjectSummary(
            project_id=project_id,
            name=name,
            path=path,
            timestamp=timestamp,
            total_files=file_count or 0,
            lines_of_code=total_size or 0,  # Using file size as proxy
            contributors_count=len(contributors),
            skills_count=len(all_skills),
            complexity_score=complexity_score,
            comprehensive_score=comprehensive_score,
            contributors=contributors,
            top_skills=all_skills[:10],
            languages=languages,
            frameworks=frameworks,
            complexity_functions=complexity_functions,
            resume_title=resume_title,
            resume_highlights=resume_highlights
        )
    
    def rank_projects(self, 
                     sort_by: SortCriteria = "comprehensive", 
                     limit: Optional[int] = None) -> List[ProjectSummary]:
        """Rank projects by specified criteria."""
        projects = self.get_all_projects()
        
        if sort_by == "complexity":
            projects.sort(key=lambda p: p.complexity_score, reverse=True)
        elif sort_by == "contributions":
            projects.sort(key=lambda p: sum(c.get('commits', 0) for c in p.contributors), reverse=True)
        elif sort_by == "skills":
            projects.sort(key=lambda p: p.skills_count, reverse=True)
        elif sort_by == "lines_of_code":
            projects.sort(key=lambda p: p.lines_of_code, reverse=True)
        elif sort_by == "file_count":
            projects.sort(key=lambda p: p.total_files, reverse=True)
        elif sort_by == "recent":
            projects.sort(key=lambda p: p.timestamp, reverse=True)
        else:  # comprehensive
            projects.sort(key=lambda p: p.comprehensive_score, reverse=True)
        
        return projects[:limit] if limit else projects
    

    

    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()





def print_project_rankings(sort_by: SortCriteria = "comprehensive", limit: Optional[int] = 10) -> None:
    """Print formatted project rankings to console."""
    summarizer = ProjectSummarizer()
    
    try:
        projects = summarizer.rank_projects(sort_by, limit)
        
        if not projects:
            print("No projects found in database.")
            return
        
        print(f"\n🏆 Top Projects (sorted by {sort_by})")
        print("=" * 60)
        
        for i, project in enumerate(projects, 1):
            print(f"\n{i}. {project.name}")
            print(f"   📅 {project.timestamp}")
            size_mb = project.lines_of_code / (1024 * 1024) if project.lines_of_code else 0
            print(f"   📊 {size_mb:.1f} MB, {project.total_files} files, {project.contributors_count} contributors")
            print(f"   🎯 Score: {project.comprehensive_score:.2f}")
            
            if project.contributors:
                top_contributor = max(project.contributors, key=lambda c: c.get('commits', 0))
                print(f"   👤 Top contributor: {top_contributor['name']} ({top_contributor.get('commits', 0)} commits)")
            
            if project.top_skills:
                print(f"   🛠️  Skills: {', '.join(project.top_skills[:5])}")
                
            if project.complexity_functions:
                top_complex = project.complexity_functions[0]
                print(f"   🧠 Most complex function: {top_complex['name']} (complexity: {top_complex['complexity']})")
    
    finally:
        summarizer.close()