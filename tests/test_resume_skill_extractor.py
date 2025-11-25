"""
Tests for the resume_skill_extractor module.

These tests verify skill extraction functionality including:
- Language skill mapping
- Framework skill detection
- File-based skill inference
- Project analysis integration
- Edge cases and error handling
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os
import json

from src.core.resume_skill_extractor import (
    extract_resume_skills,
    analyze_project_skills,
    extract_languages_from_project,
    extract_frameworks_from_project,
    get_skill_categories,
    LANGUAGE_SKILLS,
    FRAMEWORK_SKILLS,
    FILE_TYPE_SKILLS
)


class TestSkillMappings:
    """Test the skill mapping dictionaries for consistency and completeness."""
    
    def test_language_skills_structure(self):
        """Test that LANGUAGE_SKILLS has proper structure."""
        assert isinstance(LANGUAGE_SKILLS, dict)
        assert len(LANGUAGE_SKILLS) > 0
        
        for language, skills in LANGUAGE_SKILLS.items():
            assert isinstance(language, str)
            assert isinstance(skills, list)
            assert len(language) > 0
            # Skills should be strings
            for skill in skills:
                assert isinstance(skill, str)
                assert len(skill) > 0
    
    def test_framework_skills_structure(self):
        """Test that FRAMEWORK_SKILLS has proper structure."""
        assert isinstance(FRAMEWORK_SKILLS, dict)
        assert len(FRAMEWORK_SKILLS) > 0
        
        for framework, skills in FRAMEWORK_SKILLS.items():
            assert isinstance(framework, str)
            assert isinstance(skills, list)
            assert len(framework) > 0
            # Skills should be strings
            for skill in skills:
                assert isinstance(skill, str)
                assert len(skill) > 0
    
    def test_file_type_skills_structure(self):
        """Test that FILE_TYPE_SKILLS has proper structure."""
        assert isinstance(FILE_TYPE_SKILLS, dict)
        assert len(FILE_TYPE_SKILLS) > 0
        
        for file_type, skills in FILE_TYPE_SKILLS.items():
            assert isinstance(file_type, str)
            assert isinstance(skills, list)
            assert len(file_type) > 0
            # Skills should be strings
            for skill in skills:
                assert isinstance(skill, str)
                assert len(skill) > 0
    
    def test_common_languages_present(self):
        """Test that common programming languages are included."""
        common_languages = ['Python', 'JavaScript', 'Java', 'C++', 'Go']
        for lang in common_languages:
            assert lang in LANGUAGE_SKILLS
    
    def test_popular_frameworks_present(self):
        """Test that popular frameworks are included."""
        popular_frameworks = ['React', 'Flask', 'Django', 'Express', 'Spring Boot']
        for framework in popular_frameworks:
            assert framework in FRAMEWORK_SKILLS


class TestSkillExtraction:
    """Test the main skill extraction functions."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_project_analyzer(self):
        """Mock ProjectAnalyzer for testing."""
        with patch('src.core.language_analyzer.ProjectAnalyzer') as mock:
            analyzer_instance = Mock()
            mock.return_value = analyzer_instance
            yield analyzer_instance
    
    @pytest.fixture
    def mock_framework_detector(self):
        """Mock framework detector for testing."""
        with patch('src.core.framework_detector.detect_frameworks_recursive') as mock:
            yield mock
    
    def test_extract_languages_from_project(self, temp_project_dir, mock_project_analyzer):
        """Test language extraction from project."""
        # Mock the analyzer to return specific languages
        mock_project_analyzer.analyze_project_languages.return_value = {
            'Python': 10,
            'JavaScript': 5,
            'Unknown': 2
        }
        
        result = extract_languages_from_project(temp_project_dir)
        
        assert isinstance(result, list)
        assert 'Python' in result
        assert 'JavaScript' in result
        assert 'Unknown' not in result  # Should filter out Unknown
        mock_project_analyzer.analyze_project_languages.assert_called_once()
    
    def test_extract_frameworks_from_project(self, temp_project_dir, mock_framework_detector):
        """Test framework extraction from project."""
        # Mock framework detector to return specific frameworks
        mock_framework_detector.return_value = {
            'frameworks': {
                str(temp_project_dir): [
                    {'name': 'Flask', 'confidence': 0.95, 'signals': ['flask']},
                    {'name': 'React', 'confidence': 0.90, 'signals': ['react']},
                    {'name': 'Docker', 'confidence': 0.85, 'signals': ['dockerfile']}
                ]
            }
        }
        
        result = extract_frameworks_from_project(temp_project_dir)
        
        assert isinstance(result, list)
        assert result == ['Flask', 'React', 'Docker']
        mock_framework_detector.assert_called_once()
    
    def test_extract_resume_skills_with_mocked_dependencies(self, temp_project_dir, mock_project_analyzer, mock_framework_detector):
        """Test resume skill extraction with mocked dependencies."""
        # Setup mocks
        mock_project_analyzer.analyze_project_languages.return_value = {
            'Python': 10,
            'JavaScript': 5
        }
        mock_framework_detector.return_value = {
            'frameworks': {
                str(temp_project_dir): [
                    {'name': 'Flask', 'confidence': 0.95, 'signals': ['flask']},
                    {'name': 'React', 'confidence': 0.90, 'signals': ['react']}
                ]
            }
        }
        
        result = extract_resume_skills(temp_project_dir)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should contain skills from Flask and React
        assert 'Backend Development' in result or 'Component-Based Architecture' in result
    
    def test_extract_resume_skills_with_provided_languages_frameworks(self, temp_project_dir):
        """Test skill extraction when languages and frameworks are provided."""
        languages = ['Python', 'JavaScript']
        frameworks = ['Django', 'React']
        
        result = extract_resume_skills(temp_project_dir, languages, frameworks)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should extract skills based on provided data
    
    def test_analyze_project_skills_structure(self, temp_project_dir, mock_project_analyzer, mock_framework_detector):
        """Test that analyze_project_skills returns proper structure."""
        # Setup mocks
        mock_project_analyzer.analyze_project_languages.return_value = {
            'Python': 10,
            'JavaScript': 5
        }
        mock_framework_detector.return_value = {
            'frameworks': {
                str(temp_project_dir): [
                    {'name': 'Flask', 'confidence': 0.95, 'signals': ['flask']},
                    {'name': 'React', 'confidence': 0.90, 'signals': ['react']}
                ]
            }
        }
        
        result = analyze_project_skills(temp_project_dir)
        
        assert isinstance(result, dict)
        required_keys = ['languages', 'frameworks', 'skills', 'skill_categories', 'total_skills', 'project_path']
        for key in required_keys:
            assert key in result
        
        assert isinstance(result['languages'], list)
        assert isinstance(result['frameworks'], list)
        assert isinstance(result['skills'], list)
        assert isinstance(result['skill_categories'], dict)
        assert isinstance(result['total_skills'], int)
        assert isinstance(result['project_path'], str)


class TestRealProjectAnalysis:
    """Test skill extraction with real project structures."""
    
    @pytest.fixture
    def python_flask_project(self):
        """Create a realistic Python Flask project for testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create Python files
        (project_path / "app.py").write_text("""
import flask
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    return jsonify({'message': 'Hello World'})

if __name__ == '__main__':
    app.run(debug=True)
""")
        
        (project_path / "requirements.txt").write_text("""
flask==2.3.0
pandas==2.0.0
numpy==1.24.0
pytest==7.4.0
""")
        
        (project_path / "config.py").write_text("""
class Config:
    SECRET_KEY = 'dev'
    DATABASE_URL = 'sqlite:///app.db'
""")
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def react_project(self):
        """Create a realistic React project for testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create JavaScript/React files
        (project_path / "App.js").write_text("""
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
    const [data, setData] = useState([]);
    
    useEffect(() => {
        axios.get('/api/data').then(response => {
            setData(response.data);
        });
    }, []);
    
    return <div>Hello React</div>;
}

export default App;
""")
        
        (project_path / "package.json").write_text("""
{
  "name": "test-react-app",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "axios": "^1.4.0",
    "lodash": "^4.17.21"
  }
}
""")
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def multi_tech_project(self):
        """Create a project with multiple technologies."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Python backend
        (project_path / "backend" / "app.py").mkdir(parents=True).parent / "app.py"
        (project_path / "backend" / "app.py").write_text("import django")
        
        # React frontend
        (project_path / "frontend" / "src" / "App.jsx").mkdir(parents=True).parent / "App.jsx"
        (project_path / "frontend" / "src" / "App.jsx").write_text("import React from 'react'")
        
        # Docker
        (project_path / "Dockerfile").write_text("FROM python:3.11")
        (project_path / "docker-compose.yml").write_text("version: '3.8'")
        
        # Database
        (project_path / "schema.sql").write_text("CREATE TABLE users (id INT);")
        
        # Design files
        (project_path / "assets" / "logo.psd").mkdir(parents=True).parent / "logo.psd"
        (project_path / "assets" / "logo.psd").write_text("# Photoshop file")
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    @patch('src.core.language_analyzer.ProjectAnalyzer')
    @patch('src.core.framework_detector.detect_frameworks_recursive')
    def test_python_project_skill_detection(self, mock_detector, mock_analyzer, python_flask_project):
        """Test skill detection in a Python Flask project."""
        # Mock returns
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_project_languages.return_value = {'Python': 3}
        mock_detector.return_value = {
            'frameworks': {
                str(python_flask_project): [
                    {'name': 'Flask', 'confidence': 0.95, 'signals': ['flask']}
                ]
            }
        }
        
        skills = extract_resume_skills(python_flask_project)
        
        assert isinstance(skills, list)
        # Should detect backend development skills
        backend_skills = [s for s in skills if 'Backend' in s or 'API' in s]
        assert len(backend_skills) > 0


class TestSkillCategories:
    """Test skill categorization functionality."""
    
    def test_get_skill_categories_structure(self):
        """Test that get_skill_categories returns proper structure."""
        categories = get_skill_categories()
        
        assert isinstance(categories, dict)
        assert len(categories) > 0
        
        expected_categories = [
            'Programming Languages',
            'Web Development',
            'Data Science & ML',
            'DevOps & Infrastructure'
        ]
        
        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], (set, list))  # Can be either set or list


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_directory(self):
        """Test skill extraction on empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.language_analyzer.ProjectAnalyzer') as mock_analyzer:
                with patch('src.core.framework_detector.detect_frameworks_recursive') as mock_detector:
                    # Mock empty results
                    mock_analyzer_instance = Mock()
                    mock_analyzer.return_value = mock_analyzer_instance
                    mock_analyzer_instance.analyze_project_languages.return_value = {}
                    mock_detector.return_value = {'frameworks': {}}
                    
                    result = extract_resume_skills(temp_dir)
                    
                    assert isinstance(result, list)
                    # Should handle empty project gracefully
    
    def test_nonexistent_directory(self):
        """Test behavior with nonexistent directory."""
        nonexistent_path = "/this/path/does/not/exist"
        
        with patch('src.core.language_analyzer.ProjectAnalyzer') as mock_analyzer:
            with patch('src.core.framework_detector.detect_frameworks_recursive') as mock_detector:
                # Mock to raise exception or return empty
                mock_analyzer_instance = Mock()
                mock_analyzer.return_value = mock_analyzer_instance
                mock_analyzer_instance.analyze_project_languages.return_value = {}
                mock_detector.return_value = {'frameworks': {}}
                
                result = extract_resume_skills(nonexistent_path)
                
                assert isinstance(result, list)
    
    def test_path_as_string_and_pathlib(self):
        """Test that both string and Path objects work."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.core.language_analyzer.ProjectAnalyzer') as mock_analyzer:
                with patch('src.core.framework_detector.detect_frameworks_recursive') as mock_detector:
                    # Setup mocks
                    mock_analyzer_instance = Mock()
                    mock_analyzer.return_value = mock_analyzer_instance
                    mock_analyzer_instance.analyze_project_languages.return_value = {'Python': 1}
                    mock_detector.return_value = {
                        'frameworks': {
                            temp_dir: [
                                {'name': 'Flask', 'confidence': 0.95, 'signals': ['flask']}
                            ]
                        }
                    }
                    
                    # Test with string path
                    result_str = extract_resume_skills(temp_dir)
                    
                    # Test with Path object
                    result_path = extract_resume_skills(Path(temp_dir))
                    
                    assert isinstance(result_str, list)
                    assert isinstance(result_path, list)
                    assert result_str == result_path
    
    def test_duplicate_skill_handling(self):
        """Test that duplicate skills are properly handled."""
        # Test with languages/frameworks that might generate overlapping skills
        languages = ['Python', 'JavaScript']
        frameworks = ['Django', 'Flask']  # Both might add 'Backend Development'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = extract_resume_skills(temp_dir, languages, frameworks)
            
            assert isinstance(result, list)
            # Check for duplicates
            assert len(result) == len(set(result)), "Skills list should not contain duplicates"


class TestIntegration:
    """Integration tests with minimal mocking."""
    
    def test_skill_extraction_integration(self):
        """Test the full skill extraction pipeline with minimal mocking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a simple test project
            (project_path / "main.py").write_text("print('Hello World')")
            (project_path / "requirements.txt").write_text("flask==2.0.0")
            (project_path / "README.md").write_text("# Test Project")
            
            # Mock only the external dependencies
            with patch('src.core.language_analyzer.ProjectAnalyzer') as mock_analyzer:
                with patch('src.core.framework_detector.detect_frameworks_recursive') as mock_detector:
                    # Setup minimal mocks
                    mock_analyzer_instance = Mock()
                    mock_analyzer.return_value = mock_analyzer_instance
                    mock_analyzer_instance.analyze_project_languages.return_value = {'Python': 1}
                    mock_detector.return_value = {
                        'frameworks': {
                            str(project_path): [
                                {'name': 'Flask', 'confidence': 0.95, 'signals': ['flask']}
                            ]
                        }
                    }
                    
                    # Test the full analysis
                    result = analyze_project_skills(project_path)
                    
                    # Verify structure
                    assert isinstance(result, dict)
                    assert 'languages' in result
                    assert 'frameworks' in result
                    assert 'skills' in result
                    assert 'total_skills' in result
                    
                    # Verify content
                    assert 'Python' in result['languages']
                    assert 'Flask' in result['frameworks']
                    assert result['total_skills'] > 0
                    assert isinstance(result['skills'], list)


if __name__ == "__main__":
    pytest.main([__file__])