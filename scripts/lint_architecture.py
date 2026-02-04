#!/usr/bin/env python3
"""
Linting tool for layered architecture documentation.
Checks for common issues in architecture files.
"""

import re
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict


@dataclass
class LintIssue:
    """Represents a single linting issue."""

    file: Path
    line: int
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    message: str
    check_type: str


@dataclass
class LintReport:
    """Collects all linting results."""

    issues: List[LintIssue] = field(default_factory=list)
    files_checked: int = 0
    constraint_ids: Set[str] = field(default_factory=set)

    def add(self, file: Path, line: int, severity: str, message: str, check_type: str):
        self.issues.append(LintIssue(file, line, severity, message, check_type))

    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]

    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]


class ArchitectureLinter:
    """Main linter class for architecture files."""

    # Patterns for detecting constraint references
    CONSTRAINT_PATTERNS = [
        r"\b(CON-\d{3,})\b",  # CON-123
        r"\[CON-\d+\]",  # [CON-123]
        r"`CON-\d+`",  # `CON-123`
    ]

    # Pattern for TODO markers
    TODO_PATTERN = re.compile(r"\bTODO\b|@todo|# TODO|<!-- TODO", re.IGNORECASE)

    # Pattern for kebab-case validation
    KEBAB_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")

    # Pattern for markdown headers
    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")

    # Pattern for layer file naming
    LAYER_FILE_PATTERN = re.compile(r"^L\d+-.*\.md$")

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.report = LintReport()
        self.constraints_file: Optional[Path] = None

    def find_constraints_file(self) -> Optional[Path]:
        """Find constraints.yml in the project."""
        # Search in common locations
        search_paths = [
            self.base_path / "constraints.yml",
            self.base_path / "architecture" / "constraints.yml",
            self.base_path / "docs" / "constraints.yml",
        ]

        # Also search recursively (limit depth)
        for path in self.base_path.rglob("constraints.yml"):
            if path.is_file():
                return path

        for path in search_paths:
            if path.exists():
                return path

        return None

    def load_constraints(self) -> Set[str]:
        """Load constraint IDs from constraints.yml."""
        constraint_ids = set()

        self.constraints_file = self.find_constraints_file()
        if not self.constraints_file:
            return constraint_ids

        try:
            with open(self.constraints_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if isinstance(content, dict):
                # Handle different structures
                if "constraints" in content:
                    constraints = content["constraints"]
                else:
                    constraints = content

                if isinstance(constraints, list):
                    for item in constraints:
                        if isinstance(item, dict) and "id" in item:
                            constraint_ids.add(item["id"])
                        elif isinstance(item, str):
                            # Simple list of IDs
                            constraint_ids.add(item)
                elif isinstance(constraints, dict):
                    for key in constraints.keys():
                        constraint_ids.add(key)

        except Exception as e:
            self.report.add(
                self.constraints_file,
                0,
                "WARNING",
                f"Could not parse constraints.yml: {e}",
                "constraints",
            )

        return constraint_ids

    def extract_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Extract YAML frontmatter from markdown file."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    return frontmatter, parts[2]
                except yaml.YAMLError as e:
                    return None, content
        return None, content

    def check_frontmatter(
        self, file: Path, frontmatter: Optional[Dict], line_offset: int = 1
    ):
        """Validate YAML frontmatter."""
        if frontmatter is None:
            # Frontmatter is optional but recommended
            return

        # Check for common frontmatter fields
        recommended_fields = ["title", "layer", "version"]
        for field in recommended_fields:
            if field not in frontmatter:
                self.report.add(
                    file,
                    line_offset,
                    "WARNING",
                    f"Missing recommended frontmatter field: {field}",
                    "frontmatter",
                )

        # Validate layer field matches filename
        if "layer" in frontmatter and isinstance(frontmatter["layer"], str):
            layer_value = frontmatter["layer"]
            expected_prefix = f"L{layer_value}-"
            if not file.name.startswith(expected_prefix):
                self.report.add(
                    file,
                    line_offset,
                    "WARNING",
                    f"Layer {layer_value} in frontmatter does not match filename prefix {expected_prefix}",
                    "frontmatter",
                )

    def check_markdown_headers(
        self, file: Path, lines: List[str]
    ) -> List[Tuple[int, str, str]]:
        """Check markdown header formatting. Returns list of (line_num, level, text)."""
        headers = []
        prev_level = 0

        for i, line in enumerate(lines, 1):
            match = self.HEADER_PATTERN.match(line)
            if line.lstrip().startswith("#") and not match:
                self.report.add(
                    file,
                    i,
                    "WARNING",
                    "Malformed header: missing space after # or empty header text",
                    "markdown",
                )
                continue
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headers.append((i, str(level), text))

                # Check for proper spacing after #
                if not re.match(r"^#{1,6}\s+\S", line):
                    self.report.add(
                        file,
                        i,
                        "WARNING",
                        f"Malformed header: missing space after #",
                        "markdown",
                    )

                # Check for header level skipping (h1 -> h3 without h2)
                if prev_level > 0 and level > prev_level + 1:
                    self.report.add(
                        file,
                        i,
                        "WARNING",
                        f"Header level jump: H{prev_level} -> H{level}",
                        "markdown",
                    )

                # Check for empty header text
                if not text:
                    self.report.add(file, i, "WARNING", "Empty header text", "markdown")

                # Check header ends properly (no trailing #)
                if text.endswith("#") and not text.endswith("\\#"):
                    self.report.add(
                        file, i, "WARNING", "Header should not end with #", "markdown"
                    )

                prev_level = level

        return headers

    def check_constraint_references(self, file: Path, lines: List[str]):
        """Check that referenced constraints exist."""
        referenced_constraints: Set[str] = set()

        for i, line in enumerate(lines, 1):
            for pattern in self.CONSTRAINT_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Clean up the match (remove brackets, backticks)
                    clean_id = re.sub(r"[\[\]`]", "", match)
                    referenced_constraints.add(clean_id)

                    if clean_id not in self.report.constraint_ids:
                        self.report.add(
                            file,
                            i,
                            "WARNING",
                            f"Constraint {clean_id} referenced but not defined in constraints.yml",
                            "constraints",
                        )

    def check_naming_conventions(self, file: Path, lines: List[str]):
        """Check naming conventions (kebab-case preferred)."""
        # Check component names in code blocks and inline code
        for i, line in enumerate(lines, 1):
            # Look for component names in backticks
            code_matches = re.findall(r"`([^`]+)`", line)
            for match in code_matches:
                # Skip if looks like code, not a name
                if any(c in match for c in [".", "(", ")", "{", "}", ";"]):
                    continue

                # Check for spaces (should use hyphens)
                if " " in match and not self.KEBAB_CASE_PATTERN.match(
                    match.replace(" ", "-")
                ):
                    self.report.add(
                        file,
                        i,
                        "INFO",
                        f'Component name "{match}" contains spaces - consider using kebab-case',
                        "naming",
                    )
                # Check for camelCase or PascalCase (info level - preference not requirement)
                elif re.match(r"^[a-z]+[A-Z]", match):
                    self.report.add(
                        file,
                        i,
                        "INFO",
                        f'Component name "{match}" uses camelCase - kebab-case is preferred',
                        "naming",
                    )

    def check_empty_sections(self, file: Path, lines: List[str]):
        """Detect empty sections (header followed by next header)."""
        for i in range(len(lines)):
            if self.HEADER_PATTERN.match(lines[i]):
                # Check if next non-empty line is also a header
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                if j < len(lines) and self.HEADER_PATTERN.match(lines[j]):
                    self.report.add(
                        file,
                        i + 1,
                        "WARNING",
                        f'Empty section: "{lines[i].strip()}"',
                        "structure",
                    )

    def check_todo_markers(self, file: Path, lines: List[str]):
        """Detect TODO markers in final docs."""
        for i, line in enumerate(lines, 1):
            if self.TODO_PATTERN.search(line):
                self.report.add(
                    file,
                    i,
                    "WARNING",
                    f'TODO marker found: "{line.strip()[:50]}..."'
                    if len(line.strip()) > 50
                    else f'TODO marker found: "{line.strip()}"',
                    "todo",
                )

    def check_file_naming(self, file: Path):
        """Validate file naming conventions."""
        # Check if it's a layer file
        if file.name.startswith("L") and file.suffix == ".md":
            if not self.LAYER_FILE_PATTERN.match(file.name):
                self.report.add(
                    file,
                    0,
                    "WARNING",
                    f"Layer file naming should follow L#-*.md pattern (e.g., L1-overview.md)",
                    "naming",
                )

        # Check for spaces in filename
        if " " in file.name:
            self.report.add(
                file,
                0,
                "WARNING",
                f"Filename contains spaces - use kebab-case instead",
                "naming",
            )

        # Check for uppercase letters (should be lowercase)
        if file.stem != file.stem.lower():
            self.report.add(
                file,
                0,
                "INFO",
                f"Filename contains uppercase letters - lowercase is preferred",
                "naming",
            )

    def check_lists(self, file: Path, lines: List[str]):
        """Check markdown list formatting."""
        in_list = False
        list_indent = 0

        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()

            # Detect list items
            list_match = re.match(r"^(\s*)[-*+]\s", stripped)
            if list_match:
                if in_list:
                    # Check consistent indentation
                    current_indent = len(list_match.group(1))
                    if current_indent != list_indent and current_indent % 2 != 0:
                        self.report.add(
                            file,
                            i,
                            "INFO",
                            "List indentation should use consistent spacing (2 or 4 spaces)",
                            "markdown",
                        )
                else:
                    in_list = True
                    list_indent = len(list_match.group(1))
            elif stripped and not stripped.startswith(" ") and in_list:
                in_list = False

    def check_common_antipatterns(self, file: Path, lines: List[str]):
        """Detect common anti-patterns."""
        for i, line in enumerate(lines, 1):
            # Check for placeholder text
            placeholders = ["XXX", "FIXME", "HACK", "TEMP", "temporal"]
            for placeholder in placeholders:
                if placeholder in line.upper() and placeholder in line:
                    self.report.add(
                        file,
                        i,
                        "WARNING",
                        f'Placeholder text found: "{placeholder}"',
                        "antipatterns",
                    )

            # Check for broken links
            if re.search(r"\]\s*\[", line) and not re.search(r"\]\[.+\]", line):
                self.report.add(
                    file, i, "WARNING", "Possibly broken link syntax", "markdown"
                )

            # Check for inline HTML
            if re.search(r"<(?!code|pre|br|hr|img|a|em|strong)[a-zA-Z][^>]*>", line):
                self.report.add(
                    file,
                    i,
                    "INFO",
                    "Inline HTML detected - prefer pure markdown when possible",
                    "markdown",
                )

    def lint_file(self, file: Path):
        """Run all linting checks on a single file."""
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception as e:
            self.report.add(file, 0, "ERROR", f"Could not read file: {e}", "io")
            return

        self.report.files_checked += 1

        # Extract and validate frontmatter
        frontmatter, body = self.extract_frontmatter(content)
        self.check_frontmatter(file, frontmatter)

        # Run all checks
        body_lines = body.split("\n")
        self.check_markdown_headers(file, body_lines)
        self.check_constraint_references(file, body_lines)
        self.check_naming_conventions(file, body_lines)
        self.check_empty_sections(file, body_lines)
        self.check_todo_markers(file, body_lines)
        self.check_file_naming(file)
        self.check_lists(file, body_lines)
        self.check_common_antipatterns(file, body_lines)

    def find_architecture_files(self) -> List[Path]:
        """Find all architecture markdown files."""
        files = []

        # Common architecture directories
        arch_dirs = [
            self.base_path,
            self.base_path / "architecture",
            self.base_path / "docs" / "architecture",
            self.base_path / "layers",
        ]

        for dir_path in arch_dirs:
            if dir_path.exists() and dir_path.is_dir():
                # Find markdown files
                for md_file in dir_path.glob("*.md"):
                    files.append(md_file)
                # Also check subdirectories
                for md_file in dir_path.rglob("*.md"):
                    if md_file not in files:
                        files.append(md_file)

        return sorted(files)

    def run(self) -> int:
        """Run the linter and return exit code."""
        print("Linting architecture files...")

        # Load constraints first
        self.report.constraint_ids = self.load_constraints()
        if self.report.constraint_ids:
            print(
                f"  Loaded {len(self.report.constraint_ids)} constraints from constraints.yml"
            )
        else:
            print("  No constraints.yml found or empty constraints")

        # Find and lint files
        files = self.find_architecture_files()

        if not files:
            print("  No architecture markdown files found")
            return 0

        layer_files = [f for f in files if re.match(r"L\d+-", f.name)]

        for file in files:
            self.lint_file(file)

        # Generate report
        print(f"\n✓ {self.report.files_checked} file(s) checked")

        if layer_files:
            print(f"✓ {len(layer_files)} layer file(s) found")

        # Group issues by severity
        warnings = self.report.warnings()
        errors = self.report.errors()

        # Display issues
        for issue in self.report.issues:
            if issue.severity == "WARNING":
                prefix = "⚠ WARNING"
            elif issue.severity == "ERROR":
                prefix = "✗ ERROR"
            else:
                prefix = "ℹ INFO"

            location = f"{issue.file.name}"
            if issue.line > 0:
                location += f":{issue.line}"

            print(f"{prefix}: [{issue.check_type}] {location} - {issue.message}")

        # Summary
        total_issues = len(self.report.issues)
        warning_count = len(warnings)
        error_count = len(errors)

        if total_issues == 0:
            print("\n✓ Lint complete - no issues found")
        else:
            parts = []
            if error_count:
                parts.append(f"{error_count} error(s)")
            if warning_count:
                parts.append(f"{warning_count} warning(s)")
            info_count = total_issues - warning_count - error_count
            if info_count:
                parts.append(f"{info_count} info")

            print(
                f"\n{'✓' if error_count == 0 else '!'} Lint complete - {', '.join(parts)}"
            )

        # Always return 0 (soft gates)
        return 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Lint architecture files for common issues"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Base path to search for architecture files (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit code)",
    )

    args = parser.parse_args()

    base_path = Path(args.path).resolve()

    if not base_path.exists():
        print(f"Error: Path does not exist: {base_path}")
        sys.exit(1)

    linter = ArchitectureLinter(base_path)
    exit_code = linter.run()

    if args.strict and linter.report.warnings():
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
