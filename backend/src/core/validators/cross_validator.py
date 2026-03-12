"""
Cross-validation module for complementary detection system.

This module provides cross-validation between languages, frameworks, libraries,
and tools to improve detection accuracy and enable richer skill inference.

Features:
- Cross-validates framework detections against libraries and tools
- Boosts confidence scores based on multi-signal agreement
- Fills gaps in framework detection when libraries/tools indicate presence
- Provides unified skill inference based on all detection signals
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# Library → Framework Mapping
# Maps library names to expected frameworks
# =============================================================================

LIBRARY_TO_FRAMEWORK_MAP: Dict[str, str] = {
    # React ecosystem
    "react": "React",
    "react-dom": "React",
    "react-router": "React",
    "react-router-dom": "React",
    "react-redux": "React",
    "@reduxjs/toolkit": "React",
    # Next.js
    "next": "Next.js",
    "@next/font": "Next.js",
    "@next/mdx": "Next.js",
    # Vue ecosystem
    "vue": "Vue",
    "vue-router": "Vue",
    "vuex": "Vue",
    "pinia": "Vue",
    # Nuxt.js
    "nuxt": "Nuxt.js",
    "@nuxt/kit": "Nuxt.js",
    # Angular
    "@angular/core": "Angular",
    "@angular/common": "Angular",
    "@angular/router": "Angular",
    "@angular/forms": "Angular",
    # Svelte ecosystem
    "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit",
    # Express
    "express": "Express",
    # Fastify
    "fastify": "Fastify",
    # NestJS
    "@nestjs/core": "NestJS",
    "@nestjs/common": "NestJS",
    # Python frameworks
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "starlette": "FastAPI",
    # Python ML/Data
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "streamlit": "Streamlit",
    "gradio": "Gradio",
    # Testing frameworks
    "jest": "Jest",
    "vitest": "Vitest",
    "pytest": "Pytest",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "@playwright/test": "Playwright",
    "mocha": "Mocha",
    # UI Libraries
    "@mui/material": "Material-UI",
    "@material-ui/core": "Material-UI",
    "antd": "Ant Design",
    "@chakra-ui/react": "Chakra UI",
    "@mantine/core": "Mantine",
    "tailwindcss": "Tailwind CSS",
    # State management
    "redux": "Redux",
    "mobx": "MobX",
    "zustand": "Zustand",
    "recoil": "Recoil",
    # GraphQL
    "@apollo/client": "Apollo Client",
    "apollo-server": "Apollo Server",
    "graphql": "GraphQL",
    # ORM
    "prisma": "Prisma",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "mongoose": "Mongoose",
    "sqlalchemy": "SQLAlchemy",
    # Mobile
    "react-native": "React Native",
    "expo": "Expo",
    "@ionic/core": "Ionic",
    "flutter": "Flutter",
    # Desktop
    "electron": "Electron",
    "@tauri-apps/api": "Tauri",
    # Build tools (as frameworks)
    "webpack": "Webpack",
    "vite": "Vite",
    "rollup": "Rollup",
    "esbuild": "esbuild",
}


# =============================================================================
# Tool → Framework Mapping
# Maps tool config files to frameworks
# =============================================================================

TOOL_TO_FRAMEWORK_MAP: Dict[str, str] = {
    # Next.js
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "next.config.ts": "Next.js",
    # Nuxt.js
    "nuxt.config.js": "Nuxt.js",
    "nuxt.config.ts": "Nuxt.js",
    # Angular
    "angular.json": "Angular",
    # SvelteKit
    "svelte.config.js": "SvelteKit",
    "svelte.config.ts": "SvelteKit",
    # Vite
    "vite.config.js": "Vite",
    "vite.config.ts": "Vite",
    "vite.config.mjs": "Vite",
    # Webpack
    "webpack.config.js": "Webpack",
    "webpack.config.ts": "Webpack",
    # NestJS
    "nest-cli.json": "NestJS",
    # Tailwind CSS
    "tailwind.config.js": "Tailwind CSS",
    "tailwind.config.ts": "Tailwind CSS",
    "tailwind.config.cjs": "Tailwind CSS",
    # Jest
    "jest.config.js": "Jest",
    "jest.config.ts": "Jest",
    "jest.config.json": "Jest",
    # Vitest
    "vitest.config.js": "Vitest",
    "vitest.config.ts": "Vitest",
    # Pytest
    "pytest.ini": "Pytest",
    "conftest.py": "Pytest",
    # Cypress
    "cypress.json": "Cypress",
    "cypress.config.js": "Cypress",
    "cypress.config.ts": "Cypress",
    # Playwright
    "playwright.config.js": "Playwright",
    "playwright.config.ts": "Playwright",
    # Docker (as a "framework" for DevOps)
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
}


# =============================================================================
# Language → Framework Priority
# Which frameworks to prioritize based on detected languages
# =============================================================================

LANGUAGE_FRAMEWORK_PRIORITY: Dict[str, List[str]] = {
    "TypeScript": [
        "React",
        "Vue",
        "Angular",
        "Svelte",
        "Next.js",
        "NestJS",
        "Express",
        "Fastify",
        "Vite",
        "Jest",
        "Vitest",
    ],
    "JavaScript": [
        "React",
        "Vue",
        "Angular",
        "Svelte",
        "Next.js",
        "Express",
        "Fastify",
        "Webpack",
        "Jest",
        "Mocha",
    ],
    "Python": [
        "Django",
        "Flask",
        "FastAPI",
        "Pytest",
        "TensorFlow",
        "PyTorch",
        "Keras",
        "Scikit-learn",
        "Pandas",
        "NumPy",
        "SQLAlchemy",
    ],
    "Java": ["Spring Boot", "Spring", "JUnit", "Hibernate", "Maven", "Gradle"],
    "Kotlin": ["Spring Boot", "Ktor", "Gradle"],
    "Ruby": ["Rails", "Sinatra", "RSpec"],
    "PHP": ["Laravel", "Symfony", "PHPUnit"],
    "Go": ["Gin", "Echo", "Fiber", "GORM"],
    "Rust": ["Actix", "Rocket", "Axum", "Tokio"],
    "C#": ["ASP.NET Core", "Entity Framework", "xUnit", "NUnit"],
    "Swift": ["SwiftUI", "UIKit"],
    "Dart": ["Flutter"],
}


# =============================================================================
# Cross-Validation Configuration
# =============================================================================

# Boost amount when multiple signals agree
MULTI_SIGNAL_BOOST = 0.15

# Minimum confidence for gap-filled frameworks
GAP_FILL_BASE_CONFIDENCE = 0.6

# Penalty when framework detected but no supporting library/tool
NO_SUPPORT_PENALTY = 0.1


@dataclass
class CrossValidationResult:
    """Result of cross-validation for a single framework."""

    name: str
    original_confidence: float
    boosted_confidence: float
    validation_sources: List[str] = field(default_factory=list)
    is_gap_filled: bool = False


@dataclass
class EnhancedDetectionResults:
    """Enhanced detection results after cross-validation."""

    frameworks: List[Dict[str, Any]] = field(default_factory=list)
    gap_filled_frameworks: List[Dict[str, Any]] = field(default_factory=list)
    validation_summary: Dict[str, Any] = field(default_factory=dict)

    def get_all_frameworks(self) -> List[Dict[str, Any]]:
        """Get all frameworks including gap-filled ones."""
        return self.frameworks + self.gap_filled_frameworks


class CrossValidator:
    """
    Cross-validator for complementary detection system.

    Takes detection results from multiple sources and cross-validates
    them to improve accuracy and fill gaps.
    """

    def __init__(
        self,
        languages: List[str],
        frameworks: List[Dict[str, Any]],
        libraries: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        rules_path: Optional[str] = None,
    ):
        """
        Initialize cross-validator with detection results.

        Args:
            languages: List of detected programming languages
            frameworks: List of detected frameworks (dicts with name, confidence, etc.)
            libraries: List of detected libraries (dicts with name, ecosystem, etc.)
            tools: List of detected tools (dicts with name, category, etc.)
            rules_path: Optional path to cross-validation rules YAML
        """
        self.languages = set(languages) if languages else set()
        self.frameworks = frameworks or []
        self.libraries = libraries or []
        self.tools = tools or []

        # Create lookup sets for efficient checking
        self._library_names = {lib.get("name", "").lower() for lib in self.libraries}
        self._tool_names = {tool.get("name", "").lower() for tool in self.tools}
        self._tool_configs = self._extract_tool_configs()
        self._framework_names = {fw.get("name", "") for fw in self.frameworks}

        # Load custom rules if provided
        self._custom_rules = self._load_rules(rules_path) if rules_path else {}

        # Results storage
        self._validation_results: Dict[str, CrossValidationResult] = {}
        self._gap_fills: List[Dict[str, Any]] = []

    def _extract_tool_configs(self) -> Set[str]:
        """Extract config file names from detected tools."""
        configs = set()
        for tool in self.tools:
            config_file = tool.get("config_file", "")
            if config_file:
                configs.add(config_file.lower())
        return configs

    def _load_rules(self, rules_path: str) -> Dict[str, Any]:
        """Load custom cross-validation rules from YAML."""
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning("Could not load cross-validation rules: %s", e)
            return {}

    def validate_frameworks(self) -> List[CrossValidationResult]:
        """
        Cross-validate framework detections against libraries and tools.

        Returns:
            List of validation results for each framework
        """
        results = []

        for framework in self.frameworks:
            fw_name = framework.get("name", "")
            original_conf = framework.get("confidence", 1.0)

            validation = self._validate_single_framework(fw_name, original_conf)
            self._validation_results[fw_name] = validation
            results.append(validation)

        return results

    def _validate_single_framework(
        self, fw_name: str, original_confidence: float
    ) -> CrossValidationResult:
        """
        Validate a single framework against libraries and tools.

        Args:
            fw_name: Framework name
            original_confidence: Original detection confidence

        Returns:
            CrossValidationResult with boosted confidence and validation sources
        """
        validation_sources = []
        boost = 0.0

        # Check library support
        library_support = self._check_library_support(fw_name)
        if library_support:
            validation_sources.append(f"library:{library_support}")
            boost += MULTI_SIGNAL_BOOST

        # Check tool support
        tool_support = self._check_tool_support(fw_name)
        if tool_support:
            validation_sources.append(f"tool:{tool_support}")
            boost += MULTI_SIGNAL_BOOST

        # Check language support (smaller boost)
        lang_support = self._check_language_support(fw_name)
        if lang_support:
            validation_sources.append(f"language:{lang_support}")
            boost += MULTI_SIGNAL_BOOST * 0.5

        # Apply penalty if no supporting evidence found
        if not validation_sources:
            boost -= NO_SUPPORT_PENALTY

        boosted_confidence = min(1.0, max(0.0, original_confidence + boost))

        return CrossValidationResult(
            name=fw_name,
            original_confidence=original_confidence,
            boosted_confidence=boosted_confidence,
            validation_sources=validation_sources,
            is_gap_filled=False,
        )

    def _check_library_support(self, fw_name: str) -> Optional[str]:
        """Check if any library supports the framework detection."""
        # Look through the library mapping
        for lib_name, expected_fw in LIBRARY_TO_FRAMEWORK_MAP.items():
            if expected_fw == fw_name and lib_name.lower() in self._library_names:
                return lib_name
        return None

    def _check_tool_support(self, fw_name: str) -> Optional[str]:
        """Check if any tool config supports the framework detection."""
        for config_file, expected_fw in TOOL_TO_FRAMEWORK_MAP.items():
            if expected_fw == fw_name and config_file.lower() in self._tool_configs:
                return config_file
        return None

    def _check_language_support(self, fw_name: str) -> Optional[str]:
        """Check if detected languages support the framework."""
        for lang in self.languages:
            priority_frameworks = LANGUAGE_FRAMEWORK_PRIORITY.get(lang, [])
            if fw_name in priority_frameworks:
                return lang
        return None

    def fill_framework_gaps(self) -> List[Dict[str, Any]]:
        """
        Detect frameworks from libraries/tools that weren't detected directly.

        Returns:
            List of gap-filled framework dictionaries
        """
        gap_fills = []

        # Check libraries for frameworks we might have missed
        for lib_name, expected_fw in LIBRARY_TO_FRAMEWORK_MAP.items():
            if lib_name.lower() in self._library_names:
                if expected_fw not in self._framework_names:
                    # Found a library that suggests a framework we didn't detect
                    gap_fill = self._create_gap_fill(
                        expected_fw, source_type="library", source_name=lib_name
                    )
                    if gap_fill:
                        gap_fills.append(gap_fill)
                        self._framework_names.add(expected_fw)

        # Check tool configs for frameworks we might have missed
        for config_file, expected_fw in TOOL_TO_FRAMEWORK_MAP.items():
            if config_file.lower() in self._tool_configs:
                if expected_fw not in self._framework_names:
                    gap_fill = self._create_gap_fill(
                        expected_fw, source_type="tool", source_name=config_file
                    )
                    if gap_fill:
                        gap_fills.append(gap_fill)
                        self._framework_names.add(expected_fw)

        self._gap_fills = gap_fills
        return gap_fills

    def _create_gap_fill(
        self, fw_name: str, source_type: str, source_name: str
    ) -> Optional[Dict[str, Any]]:
        """Create a gap-filled framework entry."""
        # Calculate confidence based on supporting evidence
        confidence = GAP_FILL_BASE_CONFIDENCE
        validation_sources = [f"{source_type}:{source_name}"]

        # Check for additional supporting evidence
        if source_type == "library":
            tool_support = self._check_tool_support(fw_name)
            if tool_support:
                confidence += MULTI_SIGNAL_BOOST
                validation_sources.append(f"tool:{tool_support}")
        elif source_type == "tool":
            lib_support = self._check_library_support(fw_name)
            if lib_support:
                confidence += MULTI_SIGNAL_BOOST
                validation_sources.append(f"library:{lib_support}")

        # Check language support
        lang_support = self._check_language_support(fw_name)
        if lang_support:
            confidence += MULTI_SIGNAL_BOOST * 0.5
            validation_sources.append(f"language:{lang_support}")

        # Store validation result
        self._validation_results[fw_name] = CrossValidationResult(
            name=fw_name,
            original_confidence=0.0,
            boosted_confidence=min(1.0, confidence),
            validation_sources=validation_sources,
            is_gap_filled=True,
        )

        return {
            "name": fw_name,
            "confidence": min(1.0, confidence),
            "signals": validation_sources,
            "is_gap_filled": True,
            "source": f"{source_type}:{source_name}",
        }

    def boost_confidence(self) -> Dict[str, float]:
        """
        Apply confidence boosts based on multi-signal agreement.

        Returns:
            Dictionary mapping framework names to their boosted confidence scores
        """
        boosted_scores = {}

        for fw_name, result in self._validation_results.items():
            boosted_scores[fw_name] = result.boosted_confidence

        return boosted_scores

    def get_enhanced_results(self) -> EnhancedDetectionResults:
        """
        Run full cross-validation and return enhanced results.

        Returns:
            EnhancedDetectionResults with validated frameworks, gap fills, and summary
        """
        # Run validation
        self.validate_frameworks()
        gap_fills = self.fill_framework_gaps()

        # Apply boosts to original frameworks
        enhanced_frameworks = []
        for framework in self.frameworks:
            fw_name = framework.get("name", "")
            result = self._validation_results.get(fw_name)

            enhanced_fw = framework.copy()
            if result:
                enhanced_fw["original_confidence"] = result.original_confidence
                enhanced_fw["confidence"] = result.boosted_confidence
                enhanced_fw["validation_sources"] = result.validation_sources
                enhanced_fw["cross_validation_boost"] = (
                    result.boosted_confidence - result.original_confidence
                )
            enhanced_frameworks.append(enhanced_fw)

        # Build summary
        summary = {
            "total_frameworks": len(enhanced_frameworks) + len(gap_fills),
            "original_frameworks": len(self.frameworks),
            "gap_filled_frameworks": len(gap_fills),
            "frameworks_boosted": sum(
                1
                for r in self._validation_results.values()
                if r.boosted_confidence > r.original_confidence and not r.is_gap_filled
            ),
            "frameworks_penalized": sum(
                1
                for r in self._validation_results.values()
                if r.boosted_confidence < r.original_confidence
            ),
            "validation_sources_used": {
                "library": sum(
                    1
                    for r in self._validation_results.values()
                    if any("library:" in s for s in r.validation_sources)
                ),
                "tool": sum(
                    1
                    for r in self._validation_results.values()
                    if any("tool:" in s for s in r.validation_sources)
                ),
                "language": sum(
                    1
                    for r in self._validation_results.values()
                    if any("language:" in s for s in r.validation_sources)
                ),
            },
        }

        return EnhancedDetectionResults(
            frameworks=enhanced_frameworks,
            gap_filled_frameworks=gap_fills,
            validation_summary=summary,
        )

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of the cross-validation results."""
        if not self._validation_results:
            self.validate_frameworks()
            self.fill_framework_gaps()

        return {
            "frameworks_validated": len(self._validation_results),
            "gap_fills": len(self._gap_fills),
            "results": {
                name: {
                    "original": r.original_confidence,
                    "boosted": r.boosted_confidence,
                    "sources": r.validation_sources,
                    "is_gap_filled": r.is_gap_filled,
                }
                for name, r in self._validation_results.items()
            },
        }


# =============================================================================
# Convenience functions
# =============================================================================


def cross_validate_detections(
    languages: List[str],
    frameworks: List[Dict[str, Any]],
    libraries: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
) -> EnhancedDetectionResults:
    """
    Convenience function to run cross-validation on detection results.

    Args:
        languages: List of detected programming languages
        frameworks: List of detected frameworks
        libraries: List of detected libraries
        tools: List of detected tools

    Returns:
        EnhancedDetectionResults with validated and gap-filled frameworks
    """
    validator = CrossValidator(languages, frameworks, libraries, tools)
    return validator.get_enhanced_results()


def get_framework_from_library(library_name: str) -> Optional[str]:
    """Get the expected framework for a library name."""
    return LIBRARY_TO_FRAMEWORK_MAP.get(library_name.lower())


def get_framework_from_tool_config(config_file: str) -> Optional[str]:
    """Get the expected framework for a tool config file."""
    return TOOL_TO_FRAMEWORK_MAP.get(config_file.lower())


def get_priority_frameworks_for_language(language: str) -> List[str]:
    """Get priority frameworks for a detected language."""
    return LANGUAGE_FRAMEWORK_PRIORITY.get(language, [])
