#!/usr/bin/env python3
"""
Comprehensive unit tests for layered-architecture scripts.

Test Classes:
1. TestInitArchitecture - Tests project creation, file generation, error handling
2. TestValidateLayer - Tests L1-L4 validation, warning output, soft gate behavior
3. TestCheckConstraints - Tests constraint loading, collision detection, circular dependency detection
4. TestCheckpointManager - Tests save/load, state detection, missing file handling
5. TestDependencyGraph - Tests DOT output, cycle detection, --check flag
6. TestConstraintAdd - Tests constraint validation, duplicate detection, ID generation
7. TestLintArchitecture - Tests markdown checks, constraint reference validation, anti-pattern detection
"""

import os
import json
import re
import sys
import yaml
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from io import StringIO

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Import modules to test
import init_architecture
import validate_layer
import checkpoint_manager
import dependency_graph
import constraint_add
import lint_architecture
import map_architecture
import start_arch
import extract_constraints
import generate_adrs
import generate_diagrams
import check_consistency
import validate_all
import validate_dependencies
import import_plan
import arch
import validate_semantic_report
import validate_research_evidence
from check_constraints import ConstraintChecker, Constraint, Component


# =============================================================================
# Test Fixtures
# =============================================================================


class TestFixtures:
    """Test fixtures and sample data for all test classes."""

    @staticmethod
    def get_valid_l1_content():
        return """# Vision

## Vision
Our system provides fast, reliable service to users.

## Constraints
- Constraint: Response time < 200ms
- Constraint: 99.9% uptime required
- Constraint: Support 1000 concurrent users
- Constraint: Data must be encrypted at rest
- Constraint: API must be RESTful

## Principles
1. Performance first
2. Security by design
3. Scalability built-in

## Success Criteria
- Handle 10,000 requests/second
- 99.99% availability
"""

    @staticmethod
    def get_valid_l2_content():
        return """# Architecture

## Subsystems
- Auth Service: Handles authentication
- User Service: Manages user data

## Boundaries
- API Gateway boundary
- Database boundary

## Data Flow
1. Client -> API Gateway
2. API Gateway -> Services
3. Services -> Database

## Interfaces
- REST API
- GraphQL endpoint
"""

    @staticmethod
    def get_valid_l3_content():
        return """# Components

## Modules
### Auth Module
- Login functionality
- Token management

### User Module
- Profile management
- Preferences storage

## API Contracts
- POST /api/login
- GET /api/users/{id}

## Dependencies
- Auth Module depends on User Module
- User Module requires Database
"""

    @staticmethod
    def get_valid_l4_content():
        return """# Implementation

## File Structure
```
src/
├── auth/
│   ├── __init__.py
│   └── login.py
├── user/
│   ├── __init__.py
│   └── profile.py
```

## Code Patterns
- Repository pattern for data access
- Service layer for business logic
"""

    @staticmethod
    def get_valid_constraints_yml():
        return {
            "version": "1.0.0",
            "constraints": [
                {
                    "id": "CON-001",
                    "name": "Response Time",
                    "category": "performance",
                    "priority": "high",
                    "conflicting": [],
                },
                {
                    "id": "CON-002",
                    "name": "Uptime",
                    "category": "reliability",
                    "priority": "high",
                    "conflicting": [],
                },
                {
                    "id": "CON-003",
                    "name": "Security",
                    "category": "security",
                    "priority": "high",
                    "conflicting": ["CON-004"],
                },
                {
                    "id": "CON-004",
                    "name": "Fast",
                    "category": "performance",
                    "priority": "medium",
                    "conflicting": ["CON-003"],
                },
            ],
        }

    @staticmethod
    def get_valid_checkpoint_yml():
        return {
            "current_layer": "L2",
            "last_completed": "L1",
            "validation_status": {
                "L1": "PASSED",
                "L2": "IN_PROGRESS",
                "L3": "NOT_STARTED",
                "L4": "NOT_STARTED",
            },
            "constraint_registry_version": 1,
            "timestamp": "2024-01-01T00:00:00",
        }


# =============================================================================
# Test Class 1: Init Architecture
# =============================================================================


class TestInitArchitecture(unittest.TestCase):
    """Tests for init_architecture.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_create_directory_structure(self):
        """Test that project directory structure is created correctly."""
        project_name = "test_project"
        plan_dir = init_architecture.create_directory_structure(
            os.path.join(self.temp_dir, project_name)
        )

        self.assertTrue(plan_dir.exists())
        self.assertEqual(plan_dir.name, ".plan")
        self.assertTrue(plan_dir.parent.name, project_name)

    def test_create_l1_meta_architecture(self):
        """Test L1 meta-architecture file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_l1_meta_architecture(plan_dir)

        l1_file = plan_dir / "L1-meta-architecture.md"
        self.assertTrue(l1_file.exists())

        content = l1_file.read_text()
        self.assertIn("# Meta-Architecture", content)
        self.assertIn("## Vision", content)
        self.assertIn("## Constraints", content)
        self.assertIn("## Principles", content)
        self.assertIn("## Success Criteria", content)

    def test_create_l2_system_architecture(self):
        """Test L2 system architecture file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_l2_system_architecture(plan_dir)

        l2_file = plan_dir / "L2-system-architecture.md"
        self.assertTrue(l2_file.exists())

        content = l2_file.read_text()
        self.assertIn("# System Architecture", content)
        self.assertIn("## Overview", content)
        self.assertIn("## Subsystems", content)
        self.assertIn("## Interfaces", content)

    def test_create_l3_component_design(self):
        """Test L3 component design file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_l3_component_design(plan_dir)

        l3_file = plan_dir / "L3-component-design.md"
        self.assertTrue(l3_file.exists())

        content = l3_file.read_text()
        self.assertIn("# Component Design", content)
        self.assertIn("## Modules", content)
        self.assertIn("### Component A", content)

    def test_create_l4_implementation(self):
        """Test L4 implementation file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_l4_implementation(plan_dir)

        l4_file = plan_dir / "L4-implementation.md"
        self.assertTrue(l4_file.exists())

        content = l4_file.read_text()
        self.assertIn("# Implementation", content)
        self.assertIn("## File Structure", content)

    def test_create_constraints_yml(self):
        """Test constraints.yml file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_constraints_yml(plan_dir)

        constraints_file = plan_dir / "constraints.yml"
        self.assertTrue(constraints_file.exists())

        content = yaml.safe_load(constraints_file.read_text())
        self.assertEqual(content["constraints"], [])
        self.assertEqual(content["version"], "1.0.0")

    def test_create_checkpoint_yml(self):
        """Test checkpoint.yml file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_checkpoint_yml(plan_dir)

        checkpoint_file = plan_dir / "checkpoint.yml"
        self.assertTrue(checkpoint_file.exists())

        content = yaml.safe_load(checkpoint_file.read_text())
        self.assertIsNone(content["current_layer"])
        self.assertIsNone(content["last_completed"])

    def test_create_gates_yml_with_mode_and_question_depth(self):
        """Test gates.yml accepts seeded mode/question depth."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_gates_yml(plan_dir, mode="soft", question_depth="thorough")

        gates_file = plan_dir / "gates.yml"
        self.assertTrue(gates_file.exists())
        content = yaml.safe_load(gates_file.read_text())
        self.assertEqual(content["mode"], "soft")
        self.assertEqual(content["question_depth"], "thorough")

    def test_create_dependencies_yml(self):
        """Test dependencies.yml file creation."""
        plan_dir = Path(self.temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)

        init_architecture.create_dependencies_yml(plan_dir)

        dep_file = plan_dir / "dependencies.yml"
        self.assertTrue(dep_file.exists())
        content = yaml.safe_load(dep_file.read_text())
        self.assertEqual(content.get("status"), "draft")
        self.assertIn("nodes", content)
        self.assertIn("edges", content)

    def test_main_with_valid_project_name(self):
        """Test main function with valid project name."""
        project_name = os.path.join(self.temp_dir, "my_project")

        with patch.object(sys, "argv", ["init_architecture.py", project_name]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                try:
                    init_architecture.main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)

        # Check all files were created
        plan_dir = Path(project_name) / ".plan"
        self.assertTrue(plan_dir.exists())
        self.assertTrue((plan_dir / "L1-meta-architecture.md").exists())
        self.assertTrue((plan_dir / "L2-system-architecture.md").exists())
        self.assertTrue((plan_dir / "L3-component-design.md").exists())
        self.assertTrue((plan_dir / "L4-implementation.md").exists())
        self.assertTrue((plan_dir / "constraints.yml").exists())
        self.assertTrue((plan_dir / "checkpoint.yml").exists())
        self.assertTrue((plan_dir / "dependencies.yml").exists())

    def test_main_with_path_flag(self):
        """Test main function with --path to init in existing directory."""
        project_root = Path(self.temp_dir)
        with patch.object(sys, "argv", ["init_architecture.py", "--path", str(project_root)]):
            with patch("sys.stdout", new=StringIO()):
                try:
                    init_architecture.main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)

        plan_dir = project_root / ".plan"
        self.assertTrue(plan_dir.exists())
        self.assertTrue((plan_dir / "L1-meta-architecture.md").exists())

    def test_main_with_here_flag(self):
        """Test main function with --here to init in CWD."""
        os.chdir(self.temp_dir)
        with patch.object(sys, "argv", ["init_architecture.py", "--here"]):
            with patch("sys.stdout", new=StringIO()):
                try:
                    init_architecture.main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)

        plan_dir = Path(self.temp_dir) / ".plan"
        self.assertTrue(plan_dir.exists())

    def test_main_without_project_name(self):
        """Test main function exits with error when no project name provided."""
        with patch.object(sys, "argv", ["init_architecture.py"]):
            with patch("sys.stderr", new=StringIO()) as mock_stderr:
                with self.assertRaises(SystemExit) as context:
                    init_architecture.main()
                self.assertEqual(context.exception.code, 1)

    def test_main_with_exception(self):
        """Test main function handles exceptions gracefully."""
        with patch.object(sys, "argv", ["init_architecture.py", ""]):
            with patch("sys.stderr", new=StringIO()) as mock_stderr:
                with self.assertRaises(SystemExit) as context:
                    init_architecture.main()
                self.assertEqual(context.exception.code, 1)


# =============================================================================
# Test Class 2: Validate Layer
# =============================================================================


class TestValidateLayer(unittest.TestCase):
    """Tests for validate_layer.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

        # Create architecture directory
        self.arch_dir = Path(self.temp_dir) / "architecture"
        self.arch_dir.mkdir()

    def test_get_arch_dir(self):
        """Test architecture directory detection."""
        arch_dir = validate_layer.get_arch_dir()
        self.assertIsInstance(arch_dir, Path)

    def test_find_layer_file_l1(self):
        """Test finding L1 layer file."""
        # Create L1 file
        l1_file = self.arch_dir / "L1-meta-architecture.md"
        l1_file.write_text("# Vision\n\n## Vision\nTest")

        result = validate_layer.find_layer_file(self.arch_dir, "L1")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "L1-meta-architecture.md")

    def test_find_layer_file_not_found(self):
        """Test finding non-existent layer file."""
        result = validate_layer.find_layer_file(self.arch_dir, "L1")
        self.assertIsNone(result)

    def test_parse_sections(self):
        """Test section parsing from markdown."""
        content = """# Title

## Section One
Content here

### Subsection
More content

## Section Two
More content
"""
        test_file = self.arch_dir / "test.md"
        test_file.write_text(content)

        sections, full_content = validate_layer.parse_sections(test_file)

        self.assertIn("Section One", sections)
        self.assertIn("Section Two", sections)
        self.assertIn("Subsection", sections)

    def test_count_constraints(self):
        """Test constraint counting in content."""
        content = """
- Constraint: Response time < 200ms
- Constraint: 99.9% uptime
1. Constraint: Support 1000 users
"""
        count = validate_layer.count_constraints(content)
        self.assertGreaterEqual(count, 3)

    def test_check_previous_layer_complete(self):
        """Test checking if previous layer is complete."""
        # No previous layer for L1
        result = validate_layer.check_previous_layer_complete(self.arch_dir, "L1")
        self.assertIsNone(result)

        # Create L1 file for L2 check
        l1_file = self.arch_dir / "L1-meta-architecture.md"
        l1_file.write_text("# Vision")

        result = validate_layer.check_previous_layer_complete(self.arch_dir, "L2")
        self.assertTrue(result)

    def test_validate_layer_l1_success(self):
        """Test L1 validation with valid content."""
        l1_file = self.arch_dir / "L1-meta-architecture.md"
        l1_file.write_text(TestFixtures.get_valid_l1_content())

        with patch("sys.stdout", new=StringIO()):
            warnings = validate_layer.validate_layer(self.arch_dir, "L1")

        # Should return list (might be empty or have warnings)
        self.assertIsInstance(warnings, list)

    def test_validate_layer_l1_missing_decision_log(self):
        """Test L1 validation warns when Decision Log missing."""
        content = """# Vision

## Vision
Test

## Constraints
- Constraint: Response time < 200ms
- Constraint: 99.9% uptime required
- Constraint: Support 1000 concurrent users

## Principles
1. Performance first
2. Security by design
3. Scalability built-in

## Success Criteria
- Handle 10,000 requests/second
- 99.99% availability
"""
        l1_file = self.arch_dir / "L1-meta-architecture.md"
        l1_file.write_text(content)

        findings = validate_layer.validate_layer(self.arch_dir, "L1")
        self.assertTrue(any("Decision Log" in f.get("message", "") for f in findings))

    def test_validate_layer_l2_missing_tradeoff_matrix(self):
        """Test L2 validation warns when Tradeoff Matrix missing."""
        content = """# Architecture

## Subsystems
- Auth Service

## Boundaries
- API Gateway boundary

## Data Flow
Client -> API Gateway

## Interfaces
- REST API

## Decision Log
1. Decision: Use REST
"""
        l2_file = self.arch_dir / "L2-system-architecture.md"
        l2_file.write_text(content)

        findings = validate_layer.validate_layer(self.arch_dir, "L2")
        self.assertTrue(any("Tradeoff Matrix" in f.get("message", "") for f in findings))

    def test_validate_layer_l2_alias_headers(self):
        """Test L2 validation accepts common header aliases."""
        content = """# Architecture

## Subsystem Inventory
- Auth Service

## System Boundaries
- API Gateway boundary

## Data Flow Diagrams
Client -> API Gateway

## Interface Contracts
- REST API

## Migration Plan
Phased migration

## Trade-off Matrix
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A | | | |

## Decisions
1. Decision: Use REST
"""
        l2_file = self.arch_dir / "L2-system-architecture.md"
        l2_file.write_text(content)

        findings = validate_layer.validate_layer(self.arch_dir, "L2")
        self.assertFalse(any("Missing Subsystems section" in f.get("message", "") for f in findings))
        self.assertFalse(any("Missing Boundaries section" in f.get("message", "") for f in findings))
        self.assertFalse(any("Missing Data Flow section" in f.get("message", "") for f in findings))
        self.assertFalse(any("Missing Interfaces section" in f.get("message", "") for f in findings))
        self.assertFalse(any("Missing Migration Strategy section" in f.get("message", "") for f in findings))
        self.assertFalse(any("Missing Tradeoff Matrix section" in f.get("message", "") for f in findings))
        self.assertFalse(any("Missing Decision Log section" in f.get("message", "") for f in findings))

    def test_validate_layer_optional_missing_ok(self):
        """Test optional layer missing does not error when allowed."""
        result = validate_layer.validate_layer(self.arch_dir, "L0", optional_missing_ok=True)
        self.assertIsInstance(result, list)

    def test_validate_layer_l5_yaml_missing_fields(self):
        """Test L5 validation warns when required YAML fields missing."""
        content = """# L5

```yaml
layer: L5
title: Test
slos: []
observability: {}
security_controls: []
deployment: {}
data_protection: {}
cost_guardrails: []
readiness_checks: []
readiness_status: not_ready
residual_risks: []
```
"""
        l5_file = self.arch_dir / "L5-operability-readiness.md"
        l5_file.write_text(content)

        findings = validate_layer.validate_layer(self.arch_dir, "L5")
        self.assertTrue(any("Missing YAML field: decision_log" in f.get("message", "") for f in findings))
        self.assertTrue(any("Missing YAML field: risk_register" in f.get("message", "") for f in findings))

    def test_validate_layer_unknown_layer(self):
        """Test validation of unknown layer."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = validate_layer.validate_layer(self.arch_dir, "L5")

        self.assertIsNone(result)

    def test_validate_layer_file_not_found(self):
        """Test validation when layer file not found."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = validate_layer.validate_layer(self.arch_dir, "L1")

        self.assertIsNone(result)

    def test_main_valid_layer(self):
        """Test main function with valid layer."""
        l1_file = self.arch_dir / "L1-meta-architecture.md"
        l1_file.write_text(TestFixtures.get_valid_l1_content())

        with patch.object(sys, "argv", ["validate_layer.py", "--soft", "L1"]):
            with patch.object(
                validate_layer, "get_arch_dir", return_value=self.arch_dir
            ):
                with patch("sys.stdout", new=StringIO()):
                    with self.assertRaises(SystemExit) as context:
                        validate_layer.main()
                    # Should exit with 0 (soft gate)
                    self.assertEqual(context.exception.code, 0)

    def test_main_no_args(self):
        """Test main function with no arguments."""
        with patch.object(sys, "argv", ["validate_layer.py"]):
            with patch.object(validate_layer, "get_arch_dir", return_value=self.arch_dir):
                with patch("sys.stdout", new=StringIO()):
                    with self.assertRaises(SystemExit) as context:
                        validate_layer.main()
                    # No layers found in empty arch_dir -> validation fails
                    self.assertEqual(context.exception.code, 3)

    def test_soft_gate_behavior(self):
        """Test that validation returns 0 even with warnings."""
        # Create incomplete L1 file (missing sections)
        l1_file = self.arch_dir / "L1-meta-architecture.md"
        l1_file.write_text("# Vision\n\nOnly header here")

        with patch.object(sys, "argv", ["validate_layer.py", "--soft", "L1"]):
            with patch.object(
                validate_layer, "get_arch_dir", return_value=self.arch_dir
            ):
                with patch("sys.stdout", new=StringIO()):
                    with self.assertRaises(SystemExit) as context:
                        validate_layer.main()
                    # Soft gate - should exit 0 even with warnings
                    self.assertEqual(context.exception.code, 0)


# =============================================================================
# Test Class 3: Check Constraints
# =============================================================================


class TestCheckConstraints(unittest.TestCase):
    """Tests for check_constraints.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.project_root = Path(self.temp_dir)

        # Create .plan directory
        self.plan_dir = self.project_root / ".plan"
        self.plan_dir.mkdir()

    def test_constraint_dataclass(self):
        """Test Constraint dataclass initialization."""
        constraint = Constraint(
            id="CON-001",
            name="Test Constraint",
            category="performance",
            priority="high",
        )

        self.assertEqual(constraint.id, "CON-001")
        self.assertEqual(constraint.name, "Test Constraint")
        self.assertEqual(constraint.category, "performance")
        self.assertEqual(constraint.priority, "high")
        self.assertEqual(constraint.conflicting, [])

    def test_component_dataclass(self):
        """Test Component dataclass initialization."""
        component = Component(
            name="AuthService",
            layer="L2",
            constraints=["CON-001"],
            dependencies=["UserService"],
        )

        self.assertEqual(component.name, "AuthService")
        self.assertEqual(component.layer, "L2")
        self.assertEqual(component.constraints, ["CON-001"])
        self.assertEqual(component.dependencies, ["UserService"])

    def test_load_constraints_registry_success(self):
        """Test successful loading of constraints registry."""
        constraints_data = TestFixtures.get_valid_constraints_yml()
        constraints_file = self.plan_dir / "constraints.yml"

        with open(constraints_file, "w") as f:
            yaml.dump(constraints_data, f)

        checker = ConstraintChecker(self.project_root)
        result = checker.load_constraints_registry()

        self.assertTrue(result)
        self.assertEqual(len(checker.constraints), 4)
        self.assertIn("CON-001", checker.constraints)

    def test_load_constraints_registry_file_not_found(self):
        """Test loading when constraints file doesn't exist."""
        checker = ConstraintChecker(self.project_root)
        result = checker.load_constraints_registry()

        self.assertFalse(result)
        self.assertIn("not found", checker.errors[0])

    def test_load_constraints_registry_invalid_yaml(self):
        """Test loading with invalid YAML."""
        constraints_file = self.plan_dir / "constraints.yml"
        constraints_file.write_text("invalid: yaml: content: [")

        checker = ConstraintChecker(self.project_root)
        result = checker.load_constraints_registry()

        self.assertFalse(result)

    def test_scan_layer_files(self):
        """Test scanning layer files."""
        # Create test layer files
        layer_files = [
            self.plan_dir / "L1-meta-architecture.md",
            self.plan_dir / "L2-system-architecture.md",
            self.plan_dir / "L3-component-design.md",
            self.plan_dir / "L4-implementation.md",
        ]
        for idx, layer_file in enumerate(layer_files, 1):
            layer_file.write_text(f"# Layer {idx}\n\n## Component\nTest")

        checker = ConstraintChecker(self.project_root)
        files_scanned = checker.scan_layer_files()

        self.assertEqual(files_scanned, 4)

    def test_check_naming_collisions(self):
        """Test detection of naming collisions."""
        checker = ConstraintChecker(self.project_root)

        # Add components with same name in different layers
        comp1 = Component(name="AuthService", layer="L2")
        comp2 = Component(name="AuthService", layer="L3")

        checker.components["AuthService"].append(comp1)
        checker.components["AuthService"].append(comp2)

        checker.check_naming_collisions()

        self.assertEqual(len(checker.warnings), 1)
        self.assertIn("Naming collision", checker.warnings[0])

    def test_check_undefined_constraints(self):
        """Test detection of undefined constraints."""
        checker = ConstraintChecker(self.project_root)

        # Add constraint to registry
        checker.constraints["CON-001"] = Constraint(
            id="CON-001", name="Test", category="test", priority="low"
        )

        # Add component with undefined constraint
        comp = Component(name="Test", layer="L2", constraints=["CON-999"])
        checker.components["Test"].append(comp)

        checker.check_undefined_constraints()

        self.assertEqual(len(checker.warnings), 1)
        self.assertIn("CON-999", checker.warnings[0])

    def test_check_circular_dependencies(self):
        """Test detection of circular dependencies."""
        checker = ConstraintChecker(self.project_root)

        # Create circular dependency: A -> B -> A
        comp_a = Component(name="ServiceA", layer="L2", dependencies=["ServiceB"])
        comp_b = Component(name="ServiceB", layer="L2", dependencies=["ServiceA"])

        checker.components["ServiceA"].append(comp_a)
        checker.components["ServiceB"].append(comp_b)

        checker.check_circular_dependencies()

        self.assertEqual(len(checker.warnings), 1)
        self.assertIn("Circular dependency", checker.warnings[0])

    def test_check_constraint_count_warning(self):
        """Test constraint count warning when >20."""
        checker = ConstraintChecker(self.project_root)
        checker.layer_constraint_counts["L1"] = 22

        checker.check_constraint_count()

        self.assertEqual(len(checker.warnings), 1)
        self.assertIn("22 constraints", checker.warnings[0])

    def test_check_contradictions(self):
        """Test detection of constraint contradictions."""
        checker = ConstraintChecker(self.project_root)

        # Add conflicting constraints
        checker.constraints["CON-003"] = Constraint(
            id="CON-003", name="Secure", category="security", priority="high"
        )
        checker.constraints["CON-004"] = Constraint(
            id="CON-004", name="Fast", category="performance", priority="medium"
        )

        # Add component with both constraints
        comp = Component(name="Test", layer="L2", constraints=["CON-003", "CON-004"])
        checker.components["Test"].append(comp)

        checker.check_contradictions()

        self.assertEqual(len(checker.warnings), 1)
        self.assertIn("Contradiction", checker.warnings[0])

    def test_generate_report(self):
        """Test report generation."""
        checker = ConstraintChecker(self.project_root)
        checker.constraints["CON-001"] = Constraint(
            id="CON-001", name="Test", category="test", priority="low"
        )
        checker.warnings.append("Test warning")

        report = checker.generate_report(3)

        self.assertIn("Checking constraints", report)
        self.assertIn("1 constraints", report)
        self.assertIn("Test warning", report)


# =============================================================================
# Test Class 4: Checkpoint Manager
# =============================================================================


class TestCheckpointManager(unittest.TestCase):
    """Tests for checkpoint_manager.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_detect_current_state_no_files(self):
        """Test state detection when no layer files exist."""
        state = checkpoint_manager.detect_current_state()

        self.assertEqual(state["current_layer"], "L1")
        self.assertIsNone(state["last_completed"])
        self.assertEqual(state["constraint_registry_version"], 1)

    def test_detect_current_state_with_complete_l1(self):
        """Test state detection with completed L1."""
        # Create L1 file with completion marker
        plan_dir = Path(".plan")
        plan_dir.mkdir(exist_ok=True)
        l1_file = plan_dir / "L1-meta-architecture.md"
        l1_file.write_text("# L1\n\n✓ COMPLETE")

        state = checkpoint_manager.detect_current_state()

        self.assertEqual(state["current_layer"], "L2")
        self.assertEqual(state["last_completed"], "L1")
        self.assertEqual(state["validation_status"]["L1"], "PASSED")

    def test_detect_current_state_with_in_progress(self):
        """Test state detection with in-progress layer."""
        # Create L2 file with WIP marker
        plan_dir = Path(".plan")
        plan_dir.mkdir(exist_ok=True)
        l2_file = plan_dir / "L2-system-architecture.md"
        l2_file.write_text("# L2\n\nWIP")

        state = checkpoint_manager.detect_current_state()

        self.assertEqual(state["current_layer"], "L2")
        self.assertEqual(state["validation_status"]["L2"], "IN_PROGRESS")

    def test_detect_constraint_version(self):
        """Test constraint version detection."""
        # Create constraints.yml
        plan_dir = Path(".plan")
        plan_dir.mkdir()
        constraints_file = plan_dir / "constraints.yml"

        with open(constraints_file, "w") as f:
            yaml.dump({"version": 5}, f)

        version = checkpoint_manager.detect_constraint_version()
        self.assertEqual(version, 5)

    def test_ensure_checkpoint_dir(self):
        """Test checkpoint directory creation."""
        checkpoint_manager.ensure_checkpoint_dir()

        self.assertTrue(checkpoint_manager.CHECKPOINT_DIR.exists())

    def test_save_checkpoint(self):
        """Test checkpoint saving."""
        checkpoint_manager.save_checkpoint()

        self.assertTrue(checkpoint_manager.CHECKPOINT_FILE.exists())

        with open(checkpoint_manager.CHECKPOINT_FILE, "r") as f:
            data = yaml.safe_load(f)

        self.assertIn("current_layer", data)
        self.assertIn("timestamp", data)

    def test_load_checkpoint_exists(self):
        """Test loading existing checkpoint."""
        # First save a checkpoint
        checkpoint_manager.save_checkpoint()

        # Then load it
        checkpoint = checkpoint_manager.load_checkpoint()

        self.assertIsNotNone(checkpoint)
        self.assertIn("current_layer", checkpoint)

    def test_load_checkpoint_not_exists(self):
        """Test loading when checkpoint doesn't exist."""
        checkpoint = checkpoint_manager.load_checkpoint()
        self.assertIsNone(checkpoint)

    def test_display_checkpoint_with_data(self):
        """Test displaying checkpoint with valid data."""
        checkpoint = {
            "current_layer": "L2",
            "last_completed": "L1",
            "validation_status": {"L1": "PASSED", "L2": "IN_PROGRESS"},
            "constraint_registry_version": 1,
            "timestamp": "2024-01-01T00:00:00",
        }

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            checkpoint_manager.display_checkpoint(checkpoint)
            output = mock_stdout.getvalue()

        self.assertIn("L2", output)
        self.assertIn("L1", output)

    def test_display_checkpoint_none(self):
        """Test displaying when no checkpoint exists."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            checkpoint_manager.display_checkpoint(None)
            output = mock_stdout.getvalue()

        self.assertIn("No checkpoint found", output)

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        checkpoint_manager.save_checkpoint()

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            checkpoint_manager.list_checkpoints()
            output = mock_stdout.getvalue()

        self.assertIn("Checkpoint History", output)

    def test_main_save_command(self):
        """Test main function with save command."""
        with patch.object(sys, "argv", ["checkpoint_manager.py", "save"]):
            with patch("sys.stdout", new=StringIO()):
                checkpoint_manager.main()

        self.assertTrue(checkpoint_manager.CHECKPOINT_FILE.exists())

    def test_main_load_command(self):
        """Test main function with load command."""
        checkpoint_manager.save_checkpoint()

        with patch.object(sys, "argv", ["checkpoint_manager.py", "load"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                checkpoint_manager.main()
                output = mock_stdout.getvalue()

        self.assertIn("Current Checkpoint", output)

    def test_main_no_command(self):
        """Test main function with no command."""
        with patch.object(sys, "argv", ["checkpoint_manager.py"]):
            with patch("sys.stdout", new=StringIO()):
                with self.assertRaises(SystemExit) as context:
                    checkpoint_manager.main()
                self.assertEqual(context.exception.code, 1)


# =============================================================================
# Test Class 5: Dependency Graph
# =============================================================================


class TestDependencyGraph(unittest.TestCase):
    """Tests for dependency_graph.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.base_path = Path(self.temp_dir)

    def test_clean_component_name(self):
        """Test component name cleaning."""
        self.assertEqual(
            dependency_graph.clean_component_name("`auth-service`"), "auth-service"
        )
        self.assertEqual(
            dependency_graph.clean_component_name("**Auth Service**"), "Auth Service"
        )
        self.assertEqual(
            dependency_graph.clean_component_name("the auth-service"), "auth-service"
        )

    def test_extract_component_names(self):
        """Test extracting component names from text."""
        text = "The `auth-service` and `user-db` are components."
        names = dependency_graph.extract_component_names(text)

        self.assertIn("auth-service", names)
        self.assertIn("user-db", names)

    def test_parse_dependencies_simple(self):
        """Test parsing simple dependencies."""
        content = """
# Architecture

AuthService depends on Database
UserService requires Cache
"""
        deps = dependency_graph.parse_dependencies(content)

        self.assertIn("AuthService", deps)
        self.assertIn("Database", deps["AuthService"])

    def test_detect_cycles_no_cycles(self):
        """Test cycle detection with no cycles."""
        deps = {"A": ["B"], "B": ["C"], "C": []}

        cycles = dependency_graph.detect_cycles(deps)
        self.assertEqual(len(cycles), 0)

    def test_detect_cycles_with_cycle(self):
        """Test cycle detection with circular dependency."""
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}

        cycles = dependency_graph.detect_cycles(deps)
        self.assertGreater(len(cycles), 0)

    def test_topological_sort_no_cycles(self):
        """Test topological sort with no cycles."""
        deps = {"A": ["B", "C"], "B": ["C"], "C": []}

        sorted_nodes, has_cycle = dependency_graph.topological_sort(deps)

        self.assertFalse(has_cycle)
        self.assertEqual(len(sorted_nodes), 3)

    def test_topological_sort_with_cycles(self):
        """Test topological sort with cycles."""
        deps = {"A": ["B"], "B": ["A"]}

        sorted_nodes, has_cycle = dependency_graph.topological_sort(deps)

        self.assertTrue(has_cycle)

    def test_generate_dot(self):
        """Test DOT format generation."""
        deps = {"ServiceA": ["ServiceB", "Database"], "ServiceB": ["Database"]}

        dot = dependency_graph.generate_dot(deps)

        self.assertIn("digraph Architecture", dot)
        self.assertIn('"ServiceA" -> "ServiceB"', dot)
        self.assertIn('"ServiceA" -> "Database"', dot)
        self.assertIn('"ServiceB" -> "Database"', dot)

    def test_load_architecture_files(self):
        """Test loading architecture files."""
        # Create test files
        l2_file = self.base_path / "L2-system-architecture.md"
        l3_file = self.base_path / "L3-component-design.md"

        l2_file.write_text("# L2\n\n## Component")
        l3_file.write_text("# L3\n\n## Component")

        l2_content, l3_content = dependency_graph.load_architecture_files(
            self.base_path
        )

        self.assertIn("# L2", l2_content)
        self.assertIn("# L3", l3_content)

    def test_merge_dependencies(self):
        """Test merging dependencies from L2 and L3."""
        l2_deps = {"A": ["B"], "C": ["D"]}
        l3_deps = {"A": ["C"], "E": ["F"]}

        merged = dependency_graph.merge_dependencies(l2_deps, l3_deps)

        self.assertIn("A", merged)
        self.assertIn("B", merged["A"])
        self.assertIn("C", merged["A"])
        self.assertIn("C", merged)
        self.assertIn("E", merged)

    def test_main_check_flag(self):
        """Test main function with --check flag."""
        # Create test architecture files
        l2_file = self.base_path / "L2-system-architecture.md"
        l2_file.write_text("""
# System Architecture

## Components
AuthService depends on Database
""")

        with patch.object(
            sys,
            "argv",
            ["dependency_graph.py", "--check", "--path", str(self.base_path)],
        ):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    dependency_graph.main()
                self.assertEqual(context.exception.code, 0)

    def test_main_dot_output(self):
        """Test main function DOT output."""
        # Create test architecture files
        l2_file = self.base_path / "L2-system-architecture.md"
        l2_file.write_text("""
# System Architecture
AuthService depends on Database
""")

        with patch.object(
            sys, "argv", ["dependency_graph.py", "--path", str(self.base_path)]
        ):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    dependency_graph.main()
                self.assertEqual(context.exception.code, 0)

                output = mock_stdout.getvalue()
                self.assertIn("digraph Architecture", output)


# =============================================================================
# Test Class 6: Constraint Add
# =============================================================================


class TestConstraintAdd(unittest.TestCase):
    """Tests for constraint_add.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_parse_args_valid(self):
        """Test argument parsing with valid arguments."""
        with patch.object(
            sys,
            "argv",
            [
                "constraint_add.py",
                "--layer",
                "L1",
                "--type",
                "performance",
                "--text",
                "Response time < 200ms",
            ],
        ):
            args = constraint_add.parse_args()

        self.assertEqual(args.layer, "L1")
        self.assertEqual(args.type, "performance")
        self.assertEqual(args.text, "Response time < 200ms")

    def test_validate_constraint_text_valid(self):
        """Test validation with valid constraint text."""
        is_valid, error = constraint_add.validate_constraint_text(
            "Response time must be < 200ms"
        )

        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validate_constraint_text_vague_term(self):
        """Test validation rejects vague terms."""
        is_valid, error = constraint_add.validate_constraint_text("Must be fast")

        self.assertFalse(is_valid)
        self.assertIn("vague term", error)

    def test_validate_constraint_text_too_short(self):
        """Test validation rejects text that's too short."""
        is_valid, error = constraint_add.validate_constraint_text("Short")

        self.assertFalse(is_valid)
        self.assertIn("too short", error)

    def test_validate_constraint_text_no_metric(self):
        """Test validation requires measurable metric."""
        is_valid, error = constraint_add.validate_constraint_text(
            "This is a constraint description"
        )

        self.assertFalse(is_valid)
        self.assertIn("measurable", error)

    def test_validate_constraint_text_non_metric_type(self):
        """Test non-metric types allow non-numeric constraints."""
        is_valid, error = constraint_add.validate_constraint_text(
            "Must comply with SOC2", "compliance"
        )
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_load_constraints_new_file(self):
        """Test loading when constraints file doesn't exist."""
        data = constraint_add.load_constraints()

        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["constraints"], [])

    def test_load_constraints_existing_file(self):
        """Test loading existing constraints file."""
        plan_dir = Path(".plan")
        plan_dir.mkdir()
        constraints_file = plan_dir / "constraints.yml"
        test_data = {"version": "2.0.0", "constraints": [{"id": "CON-001"}]}

        with open(constraints_file, "w") as f:
            yaml.dump(test_data, f)

        data = constraint_add.load_constraints()

        self.assertEqual(data["version"], "2.0.0")
        self.assertEqual(len(data["constraints"]), 1)

    def test_save_constraints(self):
        """Test saving constraints."""
        test_data = {"version": "1.0.0", "constraints": []}
        constraint_add.save_constraints(test_data)

        self.assertTrue(constraint_add.CONSTRAINTS_FILE.exists())

    def test_check_duplicate_true(self):
        """Test duplicate detection returns True for duplicate."""
        constraints = [{"text": "Response time < 200ms"}]

        is_duplicate = constraint_add.check_duplicate(
            constraints, "Response time < 200ms"
        )

        self.assertTrue(is_duplicate)

    def test_check_duplicate_false(self):
        """Test duplicate detection returns False for unique."""
        constraints = [{"text": "Response time < 200ms"}]

        is_duplicate = constraint_add.check_duplicate(constraints, "Uptime > 99.9%")

        self.assertFalse(is_duplicate)

    def test_generate_constraint_id_first(self):
        """Test ID generation for first constraint."""
        constraints = []
        new_id = constraint_add.generate_constraint_id(constraints)

        self.assertEqual(new_id, "CON-001")

    def test_generate_constraint_id_subsequent(self):
        """Test ID generation for subsequent constraints."""
        constraints = [{"id": "CON-001"}, {"id": "CON-005"}, {"id": "CON-003"}]
        new_id = constraint_add.generate_constraint_id(constraints)

        self.assertEqual(new_id, "CON-006")

    def test_increment_version(self):
        """Test version incrementing."""
        self.assertEqual(constraint_add.increment_version("1.0.0"), "1.0.1")
        self.assertEqual(constraint_add.increment_version("2.5.9"), "2.5.10")

    def test_main_success(self):
        """Test successful constraint addition."""
        with patch.object(
            sys,
            "argv",
            [
                "constraint_add.py",
                "--layer",
                "L1",
                "--type",
                "performance",
                "--text",
                "Response time < 200ms",
            ],
        ):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                constraint_add.main()
                output = mock_stdout.getvalue()

        self.assertIn("Constraint added", output)
        self.assertIn("CON-001", output)

    def test_main_validation_error(self):
        """Test main with validation error."""
        with patch.object(
            sys,
            "argv",
            [
                "constraint_add.py",
                "--layer",
                "L1",
                "--type",
                "performance",
                "--text",
                "Fast",  # Vague term
            ],
        ):
            with patch("sys.stderr", new=StringIO()):
                with self.assertRaises(SystemExit) as context:
                    constraint_add.main()
                self.assertEqual(context.exception.code, 1)

    def test_main_duplicate_error(self):
        """Test main with duplicate constraint."""
        # First add a constraint
        with patch.object(
            sys,
            "argv",
            [
                "constraint_add.py",
                "--layer",
                "L1",
                "--type",
                "performance",
                "--text",
                "Response time < 200ms",
            ],
        ):
            constraint_add.main()

        # Try to add duplicate
        with patch.object(
            sys,
            "argv",
            [
                "constraint_add.py",
                "--layer",
                "L1",
                "--type",
                "performance",
                "--text",
                "Response time < 200ms",
            ],
        ):
            with patch("sys.stderr", new=StringIO()):
                with self.assertRaises(SystemExit) as context:
                    constraint_add.main()
                self.assertEqual(context.exception.code, 1)


# =============================================================================
# Test Class 7: Extract Constraints
# =============================================================================


class TestExtractConstraints(unittest.TestCase):
    """Tests for extract_constraints.py script."""

    def test_extract_constraints_from_text(self):
        text = """| ID | Constraint | Rationale |
|----|------------|-----------|
| CON-001 | Response time < 200ms | Performance |

- CON-002: 99.9% uptime
"""
        extracted = extract_constraints.extract_constraints_from_text(text)
        self.assertIn("CON-001", extracted)
        self.assertIn("CON-002", extracted)
        self.assertEqual(extracted["CON-001"], "Response time < 200ms")


# =============================================================================
# Test Class 8: ADR Generation
# =============================================================================


class TestGenerateADRs(unittest.TestCase):
    """Tests for generate_adrs.py script."""

    def test_generate_adrs_from_decision_log(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        plan_dir.mkdir()
        l1_file = plan_dir / "L1-meta-architecture.md"
        l1_file.write_text(
            "# Meta\n\n## Decision Log\n1. **Decision**: Use Postgres\n   - **Rationale**: ACID\n   - **Impact**: Schema design\n"
        )
        with patch.object(sys, "argv", ["generate_adrs.py", "--path", str(plan_dir)]):
            generate_adrs.main()
        adr_dir = plan_dir / "decisions"
        self.assertTrue(adr_dir.exists())
        self.assertTrue((adr_dir / "README.md").exists())


# =============================================================================
# Test Class 9: Diagram Generation
# =============================================================================


class TestGenerateDiagrams(unittest.TestCase):
    """Tests for generate_diagrams.py script."""

    def test_generate_mermaid(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        plan_dir.mkdir()
        l2_file = plan_dir / "L2-system-architecture.md"
        l2_file.write_text(
            "# System Architecture\n\n## Subsystems\n- Auth Service\n- API Gateway\n\n## Data Flow\nAuth Service -> API Gateway\n"
        )
        with patch.object(
            sys,
            "argv",
            ["generate_diagrams.py", "--path", str(plan_dir), "--format", "mermaid"],
        ):
            generate_diagrams.main()
        diagram = plan_dir / "diagrams" / "system-flow.mmd"
        self.assertTrue(diagram.exists())

 
# =============================================================================
# Test Class 10: Validate Dependencies
# =============================================================================


class TestValidateDependencies(unittest.TestCase):
    """Tests for validate_dependencies.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.plan_dir = Path(self.temp_dir) / ".plan"
        self.plan_dir.mkdir()

    def write_dep(self, content: str):
        (self.plan_dir / "dependencies.yml").write_text(content)

    def test_missing_dependencies_file(self):
        warnings, errors = validate_dependencies.validate_dependencies(self.plan_dir)
        self.assertTrue(errors)

    def test_draft_status_errors(self):
        self.write_dep(
            "version: \"1.0.0\"\nstatus: draft\nnodes:\n  - name: a\nedges: []\n"
        )
        warnings, errors = validate_dependencies.validate_dependencies(self.plan_dir)
        self.assertTrue(errors)

    def test_valid_dependencies(self):
        self.write_dep(
            "version: \"1.0.0\"\nstatus: complete\nnodes:\n  - name: a\n  - name: b\nedges:\n  - from: a\n    to: b\nconstraints:\n  acyclic: true\n"
        )
        warnings, errors = validate_dependencies.validate_dependencies(self.plan_dir)
        self.assertFalse(errors)

    def test_cycle_detection(self):
        self.write_dep(
            "version: \"1.0.0\"\nstatus: complete\nnodes:\n  - name: a\n  - name: b\nedges:\n  - from: a\n    to: b\n  - from: b\n    to: a\nconstraints:\n  acyclic: true\n"
        )
        warnings, errors = validate_dependencies.validate_dependencies(self.plan_dir)
        self.assertTrue(errors)

    def test_auto_stub_creates_file(self):
        warnings, errors = validate_dependencies.validate_dependencies(
            self.plan_dir, auto_stub=True, no_write=False
        )
        self.assertTrue((self.plan_dir / "dependencies.yml").exists())
        self.assertTrue(errors)

    def test_legacy_modules_schema_errors(self):
        self.write_dep(
            "version: \"1.0.0\"\nstatus: complete\nmodules:\n  - a\nedges: []\n"
        )
        warnings, errors = validate_dependencies.validate_dependencies(self.plan_dir)
        self.assertTrue(errors)

    def test_missing_edges_schema_errors(self):
        self.write_dep(
            "version: \"1.0.0\"\nstatus: complete\nnodes:\n  - name: a\n"
        )
        warnings, errors = validate_dependencies.validate_dependencies(self.plan_dir)
        self.assertTrue(errors)


# =============================================================================
# Test Class 11: Consistency Checks
# =============================================================================


class TestConsistencyChecks(unittest.TestCase):
    """Tests for check_consistency.py script."""

    def test_consistency_warnings(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        plan_dir.mkdir()
        (plan_dir / "constraints.yml").write_text(
            "version: \"1.0.0\"\nconstraints:\n  - id: CON-001\n    layer: L1\n    text: \"Test\"\n"
        )
        (plan_dir / "L2-system-architecture.md").write_text("CON-999")
        with patch.object(sys, "argv", ["check_consistency.py", "--path", str(plan_dir)]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                check_consistency.main()
                output = mock_stdout.getvalue()
        self.assertIn("warnings", output.lower())


# =============================================================================
# Test Class 11: Validate All
# =============================================================================


class TestValidateAll(unittest.TestCase):
    """Tests for validate_all.py script."""

    def write_minimal_plan(
        self,
        plan_dir: Path,
        *,
        include_research: bool,
        include_semantic: bool,
        gates_overrides: dict | None = None,
    ) -> None:
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "L1-meta-architecture.md").write_text(
            """# L1

## Vision
Test vision

## Constraints
- CON-001: Test constraint one
- CON-002: Test constraint two
- CON-003: Test constraint three

## Principles
1. Principle one
2. Principle two

## Success Criteria
- Success one
- Success two

## Decision Log
1. **Decision**: Choice
   - **Rationale**: Because
   - **Impact**: It impacts

## Risk Register
1. **Risk**: Risky
   - **Severity**: Low
   - **Mitigation**: Mitigate
   - **Owner**: Team
"""
        )
        (plan_dir / "L2-system-architecture.md").write_text(
            """# L2

## Overview
Overview

## Subsystems
- Core

## Boundaries
Boundaries

## Data Flow
Core -> Core

## Interfaces
- API

## External Dependencies
- Redis

## Migration Strategy
None

## Tradeoff Matrix
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A | a | b | choose |

## Decision Log
1. **Decision**: Use Redis
   - **Rationale**: Cache
   - **Impact**: Adds dependency
"""
        )
        (plan_dir / "L3-component-design.md").write_text(
            """# L3

## Modules
- ModuleA (CON-002)

## API Contracts
- ContractA

## Dependencies
- ModuleA depends on ModuleB

## Decision Log
1. **Decision**: Module design
   - **Rationale**: R
   - **Impact**: I
"""
        )
        (plan_dir / "L4-implementation.md").write_text(
            """# L4

## File Structure
```
src/
  module_a.py
```

## Code Patterns
- PatternA

## Implementation Details
- Detail (CON-003)

## Validation Commands
```bash
echo ok
```

## Implementation Order
1. [ ] Task

## Testing Strategy
- Unit tests: basic
- Integration tests: basic

## Build & Deployment
Deploy

## Decision Log
1. **Decision**: Build
   - **Rationale**: R
   - **Impact**: I
"""
        )
        (plan_dir / "constraints.yml").write_text(
            "version: \"1.0.0\"\nconstraints:\n  - id: CON-001\n    layer: L1\n    text: \"Test constraint one\"\n  - id: CON-002\n    layer: L1\n    text: \"Test constraint two\"\n  - id: CON-003\n    layer: L1\n    text: \"Test constraint three\"\n"
        )
        (plan_dir / "dependencies.yml").write_text(
            "version: \"1.0.0\"\nstatus: complete\nnodes:\n  - name: Core\nedges:\n  - from: Core\n    to: Core\nconstraints:\n  acyclic: true\n"
        )

        gates = {
            "mode": "strict",
            "question_depth": "minimal",
            "l0_required": False,
            "l5_required": False,
            "research_required": False,
            "research_approved": include_research,
            "research_approval_receipt": "research-test" if include_research else None,
            "research_approved_by": "tester" if include_research else None,
            "research_approved_at": "2026-02-11T10:00:00Z" if include_research else None,
            "semantic_required": True,
            "semantic_completed": include_semantic,
            "semantic_completion_receipt": "semantic-test" if include_semantic else None,
            "semantic_completed_by": "tester" if include_semantic else None,
            "semantic_completed_at": "2026-02-11T10:00:00Z" if include_semantic else None,
            "dependencies_complete": True,
            "constraints_registry_present": True,
            "last_validation_report": ".plan/last-validation.json",
            "last_step": "init",
        }
        if gates_overrides:
            gates.update(gates_overrides)
        (plan_dir / "gates.yml").write_text(yaml.safe_dump(gates, sort_keys=False))

        if include_research:
            (plan_dir / "research.md").write_text("# Research\n\n- source: test\n")
            (plan_dir / "research.evidence.json").write_text(
                json.dumps(
                    {
                        "version": "1.0.0",
                        "generated_at": "2026-02-11T10:00:00Z",
                        "research_scope": "Dependency selection",
                        "executor": {"mode": "manual_user_input", "task_ids": []},
                        "sources": [
                            {
                                "id": "SRC-001",
                                "title": "Example",
                                "url": "https://example.com",
                                "retrieved_at": "2026-02-11T09:00:00Z",
                            }
                        ],
                        "claims": [
                            {
                                "id": "CLM-001",
                                "text": "Example claim",
                                "source_ids": ["SRC-001"],
                                "decision_impacts": ["DEC-001"],
                            }
                        ],
                    }
                )
            )
        if include_semantic:
            (plan_dir / "semantic-validation.md").write_text(
                "# Semantic Validation Report\n\n"
                "## Shard A (L1↔L2)\nstatus: PASS\nexecutor: subagent-a\nevidence_ref: L1:Constraints\nfinding_id: NONE\n\n"
                "## Shard B (L2↔L3)\nstatus: PASS\nexecutor: subagent-b\nevidence_ref: L2:Interfaces\nfinding_id: NONE\n\n"
                "## Shard C (L3↔L4)\nstatus: PASS\nexecutor: subagent-c\nevidence_ref: L3:Modules\nfinding_id: NONE\n\n"
                "## Shard D (Constraints)\nstatus: PASS\nexecutor: subagent-d\nevidence_ref: constraints.yml\nfinding_id: NONE\n\n"
                "## Shard E (Dependencies)\nstatus: PASS\nexecutor: subagent-e\nevidence_ref: dependencies.yml\nfinding_id: NONE\n"
            )

    def test_validate_all_json_output(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        plan_dir.mkdir()
        # Minimal files to allow validate_layer to run
        (plan_dir / "L1-meta-architecture.md").write_text("# L1\n\n## Vision\nx\n")
        (plan_dir / "L2-system-architecture.md").write_text("# L2\n\n## Subsystems\n- a\n")
        (plan_dir / "L3-component-design.md").write_text("# L3\n\n## Modules\n- a\n")
        (plan_dir / "L4-implementation.md").write_text("# L4\n\n## File Structure\nx\n")

        with patch.object(sys, "argv", ["validate_all.py", "--path", str(plan_dir), "--format", "json"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                validate_all.main()
                output = mock_stdout.getvalue()
        self.assertIn("\"overall\"", output)

    def test_validate_all_strict_fails_without_semantic_report(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        self.write_minimal_plan(
            plan_dir,
            include_research=True,
            include_semantic=False,
            gates_overrides={"semantic_completed": True, "research_approved": True},
        )

        with patch.object(sys, "argv", ["validate_all.py", "--path", str(plan_dir), "--strict"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                exit_code = validate_all.main()
                output = mock_stdout.getvalue()
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Semantic Validation", output)

    def test_validate_all_strict_fails_without_research_log(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        self.write_minimal_plan(
            plan_dir,
            include_research=False,
            include_semantic=True,
            gates_overrides={"semantic_completed": True, "research_approved": True},
        )

        with patch.object(sys, "argv", ["validate_all.py", "--path", str(plan_dir), "--strict"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                exit_code = validate_all.main()
                output = mock_stdout.getvalue()
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Research", output)

    def test_validate_all_gates_schema_missing_keys(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        self.write_minimal_plan(plan_dir, include_research=True, include_semantic=True)
        (plan_dir / "gates.yml").write_text("mode: strict\n")

        with patch.object(sys, "argv", ["validate_all.py", "--path", str(plan_dir), "--strict"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                exit_code = validate_all.main()
                output = mock_stdout.getvalue()
        self.assertNotEqual(exit_code, 0)
        self.assertIn("gates.yml", output)

    def test_validate_all_json_has_blocking_findings_schema(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        self.write_minimal_plan(plan_dir, include_research=False, include_semantic=False)

        with patch.object(
            sys,
            "argv",
            ["validate_all.py", "--path", str(plan_dir), "--strict", "--format", "json"],
        ):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                exit_code = validate_all.main()
                output = mock_stdout.getvalue()
        data = json.loads(output)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("blocking_findings", data)
        self.assertIsInstance(data["blocking_findings"], list)
        if data["blocking_findings"]:
            finding = data["blocking_findings"][0]
            self.assertIn("file", finding)
            self.assertIn("section", finding)
            self.assertIn("fix_command", finding)
            self.assertIn("id", finding)

    def test_validate_all_manual_gate_tamper_is_blocking(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        self.write_minimal_plan(plan_dir, include_research=True, include_semantic=True)

        gates_path = plan_dir / "gates.yml"
        gates = yaml.safe_load(gates_path.read_text())
        gates["research_approval_receipt"] = None
        gates_path.write_text(yaml.safe_dump(gates, sort_keys=False))

        with patch.object(
            sys, "argv", ["validate_all.py", "--path", str(plan_dir), "--strict", "--format", "json"]
        ):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                exit_code = validate_all.main()
                output = mock_stdout.getvalue()
        data = json.loads(output)
        self.assertNotEqual(exit_code, 0)
        self.assertTrue(any("receipt" in f.get("id", "").lower() for f in data["blocking_findings"]))


# =============================================================================
# Test Class 12: Semantic Report Validation
# =============================================================================


class TestValidateSemanticReport(unittest.TestCase):
    """Tests for validate_semantic_report.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.plan_dir = Path(self.temp_dir) / ".plan"
        self.plan_dir.mkdir()

    def test_missing_report_errors(self):
        warnings, errors = validate_semantic_report.validate_report(self.plan_dir)
        self.assertTrue(errors)

    def test_missing_shards_warns(self):
        (self.plan_dir / "semantic-validation.md").write_text(
            "# Semantic Validation Report\n\n## Shard A\n- status: PASS\n"
        )
        warnings, errors = validate_semantic_report.validate_report(self.plan_dir)
        self.assertFalse(errors)
        self.assertTrue(warnings)

    def test_task_capable_requires_distinct_executors(self):
        (self.plan_dir / "semantic-validation.md").write_text(
            "# Semantic Validation Report\n\n"
            "## Shard A\nstatus: PASS\nexecutor: same\n evidence_ref: a\nfinding_id: NONE\n\n"
            "## Shard B\nstatus: PASS\nexecutor: same\n evidence_ref: b\nfinding_id: NONE\n\n"
            "## Shard C\nstatus: PASS\nexecutor: same\n evidence_ref: c\nfinding_id: NONE\n\n"
            "## Shard D\nstatus: PASS\nexecutor: same\n evidence_ref: d\nfinding_id: NONE\n\n"
            "## Shard E\nstatus: PASS\nexecutor: same\n evidence_ref: e\nfinding_id: NONE\n"
        )
        warnings, errors = validate_semantic_report.validate_report(
            self.plan_dir, task_capable=True
        )
        self.assertFalse(errors)
        self.assertTrue(any("one executor per shard" in w.lower() for w in warnings))


# =============================================================================
# Test Class 13: Research Evidence Validation
# =============================================================================


class TestValidateResearchEvidence(unittest.TestCase):
    """Tests for validate_research_evidence.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.plan_dir = Path(self.temp_dir) / ".plan"
        self.plan_dir.mkdir()

    def test_missing_evidence_file_errors(self):
        warnings, errors = validate_research_evidence.validate_evidence_file(self.plan_dir)
        self.assertFalse(warnings)
        self.assertTrue(errors)

    def test_invalid_claim_source_mapping_errors(self):
        evidence = {
            "version": "1.0.0",
            "generated_at": "2026-02-11T10:00:00Z",
            "research_scope": "deps",
            "executor": {"mode": "subagent", "task_ids": ["t1"]},
            "sources": [
                {
                    "id": "SRC-001",
                    "url": "https://example.com",
                    "retrieved_at": "2026-02-11T09:00:00Z",
                }
            ],
            "claims": [
                {
                    "id": "CLM-001",
                    "text": "Claim",
                    "source_ids": ["SRC-404"],
                    "decision_impacts": ["DEC-001"],
                }
            ],
        }
        path = self.plan_dir / "research.evidence.json"
        path.write_text(json.dumps(evidence))
        warnings, errors = validate_research_evidence.validate_evidence_file(self.plan_dir)
        self.assertTrue(any("unknown source id" in e.lower() for e in errors))


# =============================================================================
# Test Class 14: Import Plan
# =============================================================================


class TestImportPlan(unittest.TestCase):
    """Tests for import_plan.py script."""

    def test_import_single_layer(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        source = Path(temp_dir) / "draft.md"
        source.write_text("# L1 Meta-Architecture\n\nContent")
        target = Path(temp_dir) / ".plan"
        with patch.object(
            sys,
            "argv",
            ["import_plan.py", "--source", str(source), "--target", str(target), "--layer", "L1"],
        ):
            import_plan.main()
        self.assertTrue((target / "L1-meta-architecture.md").exists())


# =============================================================================
# Test Class 13: Lint Architecture
# =============================================================================


class TestLintArchitecture(unittest.TestCase):
    """Tests for lint_architecture.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.base_path = Path(self.temp_dir)

    def create_test_file(self, name, content):
        """Helper to create test files."""
        file_path = self.base_path / name
        file_path.write_text(content)
        return file_path

    def test_lint_issue_dataclass(self):
        """Test LintIssue dataclass."""
        issue = lint_architecture.LintIssue(
            file=Path("test.md"),
            line=10,
            severity="WARNING",
            message="Test message",
            check_type="test",
        )

        self.assertEqual(issue.line, 10)
        self.assertEqual(issue.severity, "WARNING")

    def test_lint_report_add(self):
        """Test adding issues to report."""
        report = lint_architecture.LintReport()

        report.add(Path("test.md"), 5, "WARNING", "Test", "test")

        self.assertEqual(len(report.issues), 1)
        self.assertEqual(len(report.warnings()), 1)

    def test_find_constraints_file(self):
        """Test finding constraints file."""
        # Create constraints file
        constraints_file = self.base_path / "constraints.yml"
        constraints_file.write_text("constraints: []")

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        found = linter.find_constraints_file()

        self.assertIsNotNone(found)

    def test_load_constraints(self):
        """Test loading constraints."""
        constraints_file = self.base_path / "constraints.yml"
        constraints_file.write_text("""
constraints:
  - id: CON-001
    name: Test
  - id: CON-002
    name: Test2
""")

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        constraint_ids = linter.load_constraints()

        self.assertIn("CON-001", constraint_ids)
        self.assertIn("CON-002", constraint_ids)

    def test_extract_frontmatter(self):
        """Test frontmatter extraction."""
        content = """---
title: Test
layer: L1
---

# Content
"""
        linter = lint_architecture.ArchitectureLinter(self.base_path)
        frontmatter, body = linter.extract_frontmatter(content)

        self.assertIsNotNone(frontmatter)
        self.assertEqual(frontmatter["title"], "Test")
        self.assertIn("# Content", body)

    def test_check_markdown_headers(self):
        """Test markdown header checking."""
        lines = [
            "# Title",
            "## Section 1",
            "### Subsection",
            "##Section 2",  # Malformed
            "###",  # Empty
        ]

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        headers = linter.check_markdown_headers(self.base_path / "test.md", lines)

        self.assertGreater(len(headers), 0)
        # Should have warnings for malformed headers
        self.assertGreater(len(linter.report.issues), 0)

    def test_check_constraint_references(self):
        """Test constraint reference validation."""
        # Set up known constraints
        linter = lint_architecture.ArchitectureLinter(self.base_path)
        linter.report.constraint_ids = {"CON-001", "CON-002"}

        lines = [
            "This references CON-001",
            "This references undefined CON-999",
        ]

        linter.check_constraint_references(self.base_path / "test.md", lines)

        # Should have warning for undefined constraint
        warnings = linter.report.warnings()
        self.assertEqual(len(warnings), 1)
        self.assertIn("CON-999", warnings[0].message)

    def test_check_naming_conventions(self):
        """Test naming convention checking."""
        lines = [
            "Use `camelCaseName` for components",
            "Use `kebab-case` for others",
        ]

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        linter.check_naming_conventions(self.base_path / "test.md", lines)

        # Should have info about camelCase
        info_issues = [i for i in linter.report.issues if i.severity == "INFO"]
        self.assertGreater(len(info_issues), 0)

    def test_check_empty_sections(self):
        """Test empty section detection."""
        lines = [
            "## Section 1",
            "",
            "## Section 2",
            "Content here",
        ]

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        linter.check_empty_sections(self.base_path / "test.md", lines)

        # Should detect empty Section 1
        warnings = linter.report.warnings()
        self.assertEqual(len(warnings), 1)
        self.assertIn("Empty section", warnings[0].message)

    def test_check_todo_markers(self):
        """Test TODO marker detection."""
        lines = [
            "# Title",
            "TODO: Fix this later",
            "Some content",
        ]

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        linter.check_todo_markers(self.base_path / "test.md", lines)

        warnings = linter.report.warnings()
        self.assertEqual(len(warnings), 1)
        self.assertIn("TODO", warnings[0].message)

    def test_check_file_naming(self):
        """Test file naming validation."""
        linter = lint_architecture.ArchitectureLinter(self.base_path)

        # Test layer file with wrong naming
        linter.check_file_naming(self.base_path / "L1_test.md")

        warnings = linter.report.warnings()
        self.assertGreater(len(warnings), 0)

    def test_check_common_antipatterns(self):
        """Test anti-pattern detection."""
        lines = [
            "Some XXX placeholder text",
            "FIXME: needs work",
            "Normal content",
        ]

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        linter.check_common_antipatterns(self.base_path / "test.md", lines)

        warnings = linter.report.warnings()
        self.assertGreaterEqual(len(warnings), 2)  # XXX and FIXME

    def test_lint_file(self):
        """Test full file linting."""
        content = """# Test File

## Section
Content here

TODO: Add more content
"""
        test_file = self.create_test_file("test.md", content)

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        linter.lint_file(test_file)

        self.assertEqual(linter.report.files_checked, 1)
        # Should have TODO warning
        self.assertGreater(len(linter.report.warnings()), 0)


# =============================================================================
# Test Class 8: Mapping Adapter
# =============================================================================


class TestMapArchitecture(unittest.TestCase):
    """Tests for map_architecture.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_extract_summary_lines_with_source(self):
        """Test summary extraction with citations."""
        path = Path("architecture-overview.md")
        path.write_text("# Overview\n\n- Key point\n")

        lines = map_architecture.extract_summary_lines_with_source(
            path, Path(self.temp_dir), cite=True
        )
        self.assertTrue(any("(source:" in line for line in lines))

    def test_suggest_and_apply_mapping(self):
        """Test suggest+apply generates .plan outputs."""
        Path("architecture-overview.md").write_text("# Overview\n\nText\n")

        with patch.object(sys, "argv", ["map_architecture.py", "--suggest"]):
            map_architecture.main()

        self.assertTrue(Path("plan.map.yml").exists())

        with patch.object(sys, "argv", ["map_architecture.py", "--apply"]):
            map_architecture.main()

        self.assertTrue((Path(".plan") / "L1-meta-architecture.md").exists())
        self.assertTrue((Path(".plan") / "constraints.yml").exists())
        constraints = yaml.safe_load((Path(".plan") / "constraints.yml").read_text())
        self.assertIn("constraints", constraints)
        mapping = yaml.safe_load(Path("plan.map.yml").read_text())
        self.assertIn("unmapped", mapping)


# =============================================================================
# Test Class 14: Arch CLI Wrappers
# =============================================================================


class TestArchCLI(unittest.TestCase):
    """Tests for arch.py wrapper commands."""

    def test_init_wrapper_passes_mode_and_question_depth(self):
        with patch.object(arch, "run_main", return_value=0) as mock_run:
            with patch.object(
                sys,
                "argv",
                [
                    "arch.py",
                    "init",
                    "--path",
                    ".",
                    "--mode",
                    "soft",
                    "--question-depth",
                    "thorough",
                ],
            ):
                arch.main()
        argv = mock_run.call_args[0][1]
        self.assertEqual(argv[0], "init_architecture.py")
        self.assertIn("--mode", argv)
        self.assertIn("soft", argv)
        self.assertIn("--question-depth", argv)
        self.assertIn("thorough", argv)

    def test_constraints_extract_wrapper(self):
        with patch.object(arch, "run_main", return_value=0) as mock_run:
            with patch.object(
                sys,
                "argv",
                [
                    "arch.py",
                    "constraints",
                    "extract",
                    "--path",
                    "L1-meta-architecture.md",
                    "--out",
                    "constraints.yml",
                ],
            ):
                arch.main()
        argv = mock_run.call_args[0][1]
        self.assertEqual(argv[0], "extract_constraints.py")
        self.assertIn("L1-meta-architecture.md", argv)

    def test_diagrams_wrapper(self):
        with patch.object(arch, "run_main", return_value=0) as mock_run:
            with patch.object(
                sys,
                "argv",
                ["arch.py", "diagrams", "--path", ".plan", "--format", "mermaid"],
            ):
                arch.main()
        argv = mock_run.call_args[0][1]
        self.assertEqual(argv[0], "generate_diagrams.py")
        self.assertIn("--format", argv)

    def test_semantic_validate_wrapper(self):
        with patch.object(arch, "run_main", return_value=0) as mock_run:
            with patch.object(
                sys,
                "argv",
                ["arch.py", "semantic", "validate", "--path", ".plan", "--strict"],
            ):
                arch.main()
        argv = mock_run.call_args[0][1]
        self.assertEqual(argv[0], "validate_semantic_report.py")
        self.assertIn("--strict", argv)

    def test_research_validate_wrapper(self):
        with patch.object(arch, "run_main", return_value=0) as mock_run:
            with patch.object(
                sys,
                "argv",
                ["arch.py", "research", "validate", "--path", ".plan", "--strict"],
            ):
                arch.main()
        argv = mock_run.call_args[0][1]
        self.assertEqual(argv[0], "validate_research_evidence.py")
        self.assertIn("--strict", argv)

    def test_next_prints_action_and_command(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        with patch.object(sys, "argv", ["init_architecture.py", "--path", temp_dir]):
            with patch("sys.stdout", new=StringIO()):
                try:
                    init_architecture.main()
                except SystemExit:
                    pass

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            arch.cmd_next(SimpleNamespace(path=str(Path(temp_dir) / ".plan")))
            output = mock_stdout.getvalue()
        self.assertIn("REQUIRED ACTION:", output)
        self.assertIn("COMMAND:", output)

    def test_external_dependencies_placeholder_does_not_trigger_research(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        plan_dir = Path(temp_dir) / ".plan"
        plan_dir.mkdir(parents=True)
        (plan_dir / "L2-system-architecture.md").write_text(
            """# System Architecture

## External Dependencies
- [Dependency 1]: [Purpose and version constraint]
- [Dependency 2]: [Purpose and version constraint]
"""
        )
        self.assertFalse(arch.has_external_deps_section(plan_dir))


# =============================================================================
# Test Class 9: Guided Start
# =============================================================================


class TestStartArch(unittest.TestCase):
    """Tests for start_arch.py script."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_start_arch_detects_docs(self):
        """Detect existing docs without .plan."""
        Path("Docs").mkdir()
        Path("Docs/overview.md").write_text("# Overview")

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            start_arch.main()
            output = mock_stdout.getvalue()

        self.assertIn("existing documentation is present", output)

    def test_start_arch_detects_plan(self):
        """Detect existing .plan directory."""
        Path(".plan").mkdir()

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            start_arch.main()
            output = mock_stdout.getvalue()

        self.assertIn("Detected existing .plan directory", output)

    def test_start_arch_fresh(self):
        """Detect fresh start with no docs."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            start_arch.main()
            output = mock_stdout.getvalue()

        self.assertIn("No .plan directory and no documentation detected", output)

    def test_find_architecture_files(self):
        """Test finding architecture files."""
        # Create test files
        (self.base_path / "L1-test.md").write_text("# L1")
        (self.base_path / "L2-test.md").write_text("# L2")

        linter = lint_architecture.ArchitectureLinter(self.base_path)
        files = linter.find_architecture_files()

        self.assertEqual(len(files), 2)

    def test_run_no_files(self):
        """Test running linter with no files."""
        linter = lint_architecture.ArchitectureLinter(self.base_path)

        with patch("sys.stdout", new=StringIO()):
            exit_code = linter.run()

        self.assertEqual(exit_code, 0)

    def test_run_with_issues(self):
        """Test running linter with issues found."""
        # Create test file with issues
        content = "# Test\n\n## Section\n\n## Next\n\nTODO: fix"
        (self.base_path / "L1-test.md").write_text(content)

        linter = lint_architecture.ArchitectureLinter(self.base_path)

        with patch("sys.stdout", new=StringIO()):
            exit_code = linter.run()

        self.assertEqual(exit_code, 0)  # Soft gate
        self.assertGreater(len(linter.report.warnings()), 0)

    def test_main_success(self):
        """Test main function."""
        # Create test file
        (self.base_path / "L1-test.md").write_text("# Test\n\nContent")

        with patch.object(sys, "argv", ["lint_architecture.py", str(self.base_path)]):
            with patch("sys.stdout", new=StringIO()):
                with self.assertRaises(SystemExit) as context:
                    lint_architecture.main()
                self.assertEqual(context.exception.code, 0)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    # Configure test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestInitArchitecture))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckConstraints))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckpointManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestConstraintAdd))
    suite.addTests(loader.loadTestsFromTestCase(TestExtractConstraints))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateADRs))
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateDiagrams))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestConsistencyChecks))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateAll))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateSemanticReport))
    suite.addTests(loader.loadTestsFromTestCase(TestImportPlan))
    suite.addTests(loader.loadTestsFromTestCase(TestLintArchitecture))
    suite.addTests(loader.loadTestsFromTestCase(TestArchCLI))

    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
