import pytest
import os
import sys

# NEED TO CHANGE ONCE IN DEVELOPMENT WTO TEST WITH FILEPATH AND LANGUAGE DETECTED

# Path setup - got file not found error and this solved it
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CORE_DIR = os.path.join(PROJECT_ROOT, 'src', 'core') 
## Insert the 'src/core' directory into the system path to allow direct module import.
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

try:
    from skill_extractor_java import analyze_code_file
except ImportError:
    pytest.fail("Error: Could not import skill_extractor_java")


JAVA_CODE_PATH_REL = "src/sample_java.java"
SKILL_MAP_PATH_REL = "src/data/skill_mapping_java.json"

# NCLOC value manually counted for verification.
EXPECTED_NCLOC = 35

# Expected raw counts based on the contents and the mapping file (manually counted)
EXPECTED_COUNTS = {
    "Object-Oriented Programming (OOP)": 10,
    "Concurrency & Multithreading": 4,
    "Exception Handling & Robustness": 2,
    "Functional Programming (Streams)": 1,
    "Data Structures & Algorithms": 8,
    "CLI / Utility": 7,
}

@pytest.fixture(scope="module")
def paths_and_expectations():
    """
    Fixture that resolves relative paths to absolute paths and verifies file existence.
    """
    # The relative path is resolved from the PROJECT_ROOT
    code_path = os.path.join(PROJECT_ROOT, JAVA_CODE_PATH_REL)
    map_path = os.path.join(PROJECT_ROOT, SKILL_MAP_PATH_REL)

    # Verify files exist before running tests
    if not os.path.exists(code_path):
        pytest.fail(f"Required file not found: {code_path}")
    if not os.path.exists(map_path):
        pytest.fail(f"Required file not found: {map_path}")

    return {
        "code_path": code_path,
        "map_path": map_path,
        "ncloc": EXPECTED_NCLOC,
        "counts": EXPECTED_COUNTS
    }


def test_analyze_java_file(paths_and_expectations):
    """
    Integration test: Analyzes a standard Java source file and asserts
    the total LOC and specific skill counts based on the expected values.
    """
    
    config = paths_and_expectations
    
    # Action: Run the analysis
    analysis_results = analyze_code_file(
        config["code_path"],
        config["map_path"]
    )
    # 1. Assert no error occurred
    assert "error" not in analysis_results, f"Analysis failed with error: {analysis_results.get('error')}"
    
    # 2. Check the total LOC (NCLOC)
    assert analysis_results['total_lines_of_code'] == config["ncloc"], (
        f"Mismatched LOC. Expected {config['ncloc']}, "
        f"but got {analysis_results['total_lines_of_code']}."
    )

    # 3. Check expected skill counts
    for skill, expected_count in config["counts"].items():
        skill_score = analysis_results['skill_scores'].get(skill)
        
        assert skill_score is not None, f"Skill '{skill}' not found in results."
        assert skill_score['raw_count'] == expected_count, (
            f"Mismatched raw count for '{skill}'. Expected {expected_count}, "
            f"but got {skill_score['raw_count']}."
        )
        # Check density score is calculated and non-negative
        assert isinstance(skill_score['density_score'], (int, float))
        assert skill_score['density_score'] >= 0