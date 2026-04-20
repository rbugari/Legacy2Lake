#!/usr/bin/env python3
"""
Prompt Consistency Validator for Legacy2Lake v4.4

This script validates that all prompts are consistent with the v4.4 runtime,
specifically around intelligent_reengineering mode and cross-agent alignment.

Usage:
    python scripts/validate_prompt_consistency.py

Exit Code:
    0 = All checks passed
    1 = Warnings found (non-blocking)
    2 = Critical errors found
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Configuration
PROMPTS_DIR = Path(__file__).parent.parent / "apps" / "api" / "prompts"
EXPECTED_AGENTS = [
    "agent_a_discovery.md",
    "agent_c_interpreter.md",
    "agent_d_auditor.md",
    "agent_f_critic.md",
    "agent_g_governance.md",
    "agent_qa_assessment.md",
    "agent_s_scout.md",
]

POST_DRAFTING_MODES = {
    "drafting_delivery": "Terminal path (no refinement)",
    "structured_refinement": "Medallion-focused modernization (Bronze/Silver/Gold)",
    "intelligent_reengineering": "Architectural consolidation and redesign",
}

CRITICAL_KEYWORDS = {
    "agent_c_interpreter.md": [
        "Direct Mode Override",
        "Intelligent Reengineering Mode",
        "Consolidation Strategy",
        "Manifest Traceability",
    ],
    "agent_f_critic.md": [
        "Layer-Aware Validation Strategy",
        "Direct Translation",
        "Architectural Enhancement",
        "Intelligent Reengineering Mode Validation",
    ],
}

CONSISTENCY_CHECKS = {
    "agent_c_interpreter.md": {
        "keywords": [
            "consolidation",
            "reusable entities",
            "shared dimensions",
            "traceability",
            "manifest",
        ],
        "should_not_contain": ["one-file-in, three-files-out", "naive split"],
    },
    "agent_f_critic.md": {
        "keywords": [
            "layer",
            "mode",
            "consolidation",
            "traceability",
            "score",
            "APPROVED",
        ],
        "should_not_contain": [],
    },
}


class PromptValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def log_error(self, msg: str):
        self.errors.append(f"❌ {msg}")

    def log_warning(self, msg: str):
        self.warnings.append(f"⚠️  {msg}")

    def log_passed(self, msg: str):
        self.passed.append(f"✅ {msg}")

    def validate_file_exists(self, file_path: Path) -> bool:
        """Check if a prompt file exists."""
        if file_path.exists():
            self.log_passed(f"Prompt file exists: {file_path.name}")
            return True
        else:
            self.log_error(f"Prompt file missing: {file_path.name}")
            return False

    def validate_required_sections(self, file_path: Path, required_sections: List[str]) -> bool:
        """Check if a file contains required sections (headers)."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            missing = []
            for section in required_sections:
                # Look for markdown headers containing the section name
                if f"## {section}" not in content and f"### {section}" not in content:
                    missing.append(section)

            if missing:
                self.log_warning(
                    f"{file_path.name}: Missing sections: {', '.join(missing)}"
                )
                return False
            else:
                self.log_passed(
                    f"{file_path.name}: All required sections present"
                )
                return True
        except Exception as e:
            self.log_error(f"Error reading {file_path.name}: {e}")
            return False

    def validate_keyword_presence(self, file_path: Path, keywords: List[str]) -> Tuple[bool, Dict]:
        """Check if a file contains expected keywords (case-insensitive)."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            found = {}
            for keyword in keywords:
                found[keyword] = keyword.lower() in content

            missing_keywords = [k for k, v in found.items() if not v]

            if missing_keywords:
                self.log_warning(
                    f"{file_path.name}: Missing keywords: {', '.join(missing_keywords)}"
                )
                return False, found
            else:
                self.log_passed(
                    f"{file_path.name}: All critical keywords found"
                )
                return True, found
        except Exception as e:
            self.log_error(f"Error reading {file_path.name}: {e}")
            return False, {}

    def validate_mode_consistency(self, file_path: Path) -> bool:
        """Check if post_drafting_mode values are consistently referenced."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            mode_refs = {}
            for mode in POST_DRAFTING_MODES.keys():
                # Count occurrences (case-insensitive)
                count = len(re.findall(rf"\b{mode}\b", content, re.IGNORECASE))
                mode_refs[mode] = count

            expected_modes_for_file = {
                "agent_c_interpreter.md": ["direct", "intelligent_reengineering", "structured_refinement"],
                "agent_f_critic.md": ["direct", "intelligent_reengineering", "intelligent_reengineering"],
            }

            if file_path.name not in expected_modes_for_file:
                return True

            # Log mode references found
            modes_found = [m for m, c in mode_refs.items() if c > 0]
            if modes_found:
                self.log_passed(
                    f"{file_path.name}: Mode references: {', '.join(modes_found)}"
                )
                return True
            else:
                self.log_warning(
                    f"{file_path.name}: No post_drafting_mode references found"
                )
                return False
        except Exception as e:
            self.log_error(f"Error validating modes in {file_path.name}: {e}")
            return False

    def validate_json_output_format(self) -> bool:
        """Check Agent C and F return valid JSON output format."""
        # For Agent C
        agent_c_path = PROMPTS_DIR / "agent_c_interpreter.md"
        try:
            with open(agent_c_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "```json" in content and '"code"' in content:
                self.log_passed(
                    "Agent C: JSON output format documented"
                )
                return True
            else:
                self.log_warning(
                    "Agent C: JSON output format may not be clearly documented"
                )
                return False
        except Exception as e:
            self.log_error(f"Error checking Agent C JSON format: {e}")
            return False

    def validate_layer_awareness(self) -> bool:
        """Check if Agent F correctly validates layer-specific behavior."""
        agent_f_path = PROMPTS_DIR / "agent_f_critic.md"
        try:
            with open(agent_f_path, "r", encoding="utf-8") as f:
                content = f.read()

            layer_checks = [
                'layer == "direct"',
                'layer IN ["bronze", "silver", "gold"]',
                "MERGE",
                "Zero-Hardcode",
            ]

            found_checks = sum(1 for check in layer_checks if check in content)

            if found_checks >= len(layer_checks) - 1:  # Allow 1 miss
                self.log_passed(
                    f"Agent F: Layer-aware validation checks present ({found_checks}/{len(layer_checks)})"
                )
                return True
            else:
                self.log_warning(
                    f"Agent F: Layer-aware checks incomplete ({found_checks}/{len(layer_checks)})"
                )
                return False
        except Exception as e:
            self.log_error(f"Error validating Agent F layer awareness: {e}")
            return False

    def validate_prompt_file(self, file_path: Path) -> bool:
        """Run all validation checks on a single prompt file."""
        if not self.validate_file_exists(file_path):
            return False

        # File-specific validations
        if file_path.name in CRITICAL_KEYWORDS:
            required = CRITICAL_KEYWORDS[file_path.name]
            self.validate_required_sections(file_path, required)

        if file_path.name in CONSISTENCY_CHECKS:
            config = CONSISTENCY_CHECKS[file_path.name]
            self.validate_keyword_presence(file_path, config["keywords"])

        self.validate_mode_consistency(file_path)
        return True

    def validate_all_prompts(self) -> int:
        """Validate all agent prompts."""
        if not PROMPTS_DIR.exists():
            self.log_error(f"Prompts directory not found: {PROMPTS_DIR}")
            return 2

        # Check each expected agent prompt
        for agent_file in EXPECTED_AGENTS:
            file_path = PROMPTS_DIR / agent_file
            self.validate_prompt_file(file_path)

        # Cross-file consistency checks
        self.validate_json_output_format()
        self.validate_layer_awareness()

        # Determine exit code
        if self.errors:
            return 2
        elif self.warnings:
            return 1
        else:
            return 0

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("Legacy2Lake v4.4 - Prompt Consistency Validation Report")
        print("=" * 80 + "\n")

        # Passed checks
        if self.passed:
            print("✅ PASSED CHECKS")
            for msg in self.passed:
                print(f"  {msg}")
            print()

        # Warnings
        if self.warnings:
            print("⚠️  WARNINGS")
            for msg in self.warnings:
                print(f"  {msg}")
            print()

        # Errors
        if self.errors:
            print("❌ ERRORS")
            for msg in self.errors:
                print(f"  {msg}")
            print()

        # Summary
        print("-" * 80)
        print(f"Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("-" * 80 + "\n")


def main():
    validator = PromptValidator()
    exit_code = validator.validate_all_prompts()
    validator.print_report()

    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
