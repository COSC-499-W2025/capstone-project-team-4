# TEST OVERVIEW: JAVA OOP SKILL EXTRACTOR
# --------------------------------------------------------------------------
# PURPOSE: To identify Object-Oriented Programming (OOP) principles by scanning Java source code.
#
# METHOD: This script employs a heuristic approach using Regular Expressions (regex)
#         to identify the presence and frequency of 15 key Java OOP constructs
#         (e.g., 'private', 'extends', 'interface').

import re
import os

# --- 1. Define the Keywords and Mapping ---
# This dictionary maps a readable name (the OOP construct) to its corresponding
# Regular Expression (regex) pattern used for searching the Java file.
# We use regex word boundaries (\b) and specific syntax (like \s+ for spaces)
# to ensure we capture actual code constructs and not just text inside strings.

OOP_IDENTIFIERS = {
    # Core Structure & Instantiation
    "class MyClass {}": r'class\s+[\w$]+',                  # Finds 'class' followed by one or more spaces and a word (the name)
    "new MyClass()": r'new\s+[\w$]+',                       # Finds 'new' followed by a class name
    "this.field": r'this\.',                                # Finds 'this.' used to reference instance members
    
    # Encapsulation / Access Modifiers
    "public": r'\bpublic\b',                                 # Finds 'public' as a whole word
    "private": r'\bprivate\b',                              # Finds 'private' as a whole word
    "protected": r'\bprotected\b',                          # Finds 'protected' as a whole word
    
    # Inheritance & Abstraction
    "extends BaseClass": r'\bextends\b',                    # Finds the 'extends' keyword
    "implements Interface": r'\bimplements\b',              # Finds the 'implements' keyword
    "interface InterfaceName {}": r'interface\s+[\w$]+',    # Finds 'interface' followed by a name
    "abstract class AbstractName {}": r'abstract\s+class',  # Finds the combined keywords 'abstract class'
    
    # Polymorphism & Control
    "@Override": r'@Override\b',                            # Finds the @Override annotation
    "super(...)": r'\bsuper\b',                             # Finds the 'super' keyword (used for constructors or methods)
    "instanceof": r'\binstanceof\b',                        # Finds the 'instanceof' keyword
    "enum Colors {}": r'enum\s+[\w$]+',                     # Finds 'enum' followed by a name
    "final class": r'final\s+class',                        # Finds the combined keywords 'final class' (prevents inheritance)
}

# --- 2. The Core Extraction Function ---
def extract_oop_identifiers(file_path):
    """
    Reads a Java file, searches for OOP identifiers using defined regex patterns,
    and prints a summary of which OOP constructs were found.
    """
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at path: {file_path}")
        return

    print(f"Analyzing Java file: {file_path}")
    print("-" * 40)
    
    try:
        # Read the entire Java file content
        with open(file_path, 'r', encoding='utf-8') as f:
            java_code = f.read()
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return

    # Dictionary to store results: {identifier: count}
    found_keywords = {}
    
    # Simple cleaning: Remove comments to reduce false positives.
    # NOTE: This only removes single-line comments (//) and multi-line comments (/* */).
    code_to_scan = re.sub(r'//.*|\/\*[\s\S]*?\*\/', '', java_code)

    # Loop through each defined identifier pattern
    for identifier_name, pattern in OOP_IDENTIFIERS.items():
        # Use re.findall to find all non-overlapping matches of the pattern in the code
        matches = re.findall(pattern, code_to_scan)
        count = len(matches)
        
        if count > 0:
            found_keywords[identifier_name] = count

    # --- 3. Output Results ---
    if not found_keywords:
        print("No specific OOP identifiers found.")
        return

    print("OOP Skill Identified by the Following Constructs:")
    print("\n| Construct | Count | Principle Signaled |")
    print("| :--- | :--- | :--- |")
    
    # Print results, adding a conceptual principle for better context
    for identifier, count in found_keywords.items():
        # Logic to assign a broad OOP principle for clarity in the output table
        if identifier.startswith("class") or "new" in identifier or "enum" in identifier:
            principle = "Core Structure"
        elif "private" in identifier or "protected" in identifier or "this" in identifier:
            principle = "Encapsulation"
        elif "extends" in identifier or "implements" in identifier or "super" in identifier or "interface" in identifier:
            principle = "Inheritance/Abstraction"
        elif "@Override" in identifier or "instanceof" in identifier:
            principle = "Polymorphism"
        elif "final" in identifier:
            principle = "Type Control"
        else:
            principle = "General"
            
        print(f"| `{identifier}` | {count} | {principle} |")

# --- 4. Execution Block ---
# This block creates a temporary Java file, runs the analyzer, and cleans up.
if __name__ == "__main__":
    # Define a sample Java file content for demonstration purposes
    DUMMY_JAVA_CONTENT = """
    /*
     * This is a multi-line comment block.
     * It should be ignored by the scanner.
     */
    package com.university;

    // This is a single-line comment
    public final class Student extends Person implements Comparable {
        private String studentId;
        protected List<String> courses; // courses field

        // Constructor demonstrates 'this' and 'super'
        public Student(String studentId, String name) {
            super(name); 
            this.studentId = studentId;
        }

        @Override // Demonstrates Polymorphism
        public int compareTo(Object obj) {
            // New keyword is used here:
            if (obj instanceof Student) {
                return this.studentId.compareTo(((Student) obj).studentId);
            }
            return 0;
        }
    }

    interface GradeCalculator {}
    enum SemesterType { FALL, SPRING }
    """
    DUMMY_FILE_PATH = "DummyStudent.java"
    
    # Write the content to a temporary file
    with open(DUMMY_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(DUMMY_JAVA_CONTENT)
        
    # Run the extraction function
    extract_oop_identifiers(DUMMY_FILE_PATH)
    
    # Clean up the dummy file
    os.remove(DUMMY_FILE_PATH)