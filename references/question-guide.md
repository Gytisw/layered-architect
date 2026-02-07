# Guided Questioning Guide

Use this guide to ask users focused questions before drafting each layer.
Pick a **question depth** at the start (minimal or thorough).

## Interactive Questioning Protocol (Required)

When the platform supports an interactive Question tool, **use it** for any
question with discrete options. Do not proceed to a new layer until:
- The core concept is unambiguous
- Scale or load is quantified
- At least 3 measurable constraints exist
- The user confirms: "Proceed to L#"

If the user answers with vague language ("fast", "scalable", "secure"),
ask a forced-choice follow-up to quantify it.

Interactive flows and decision trees: `references/interactive-questions.md`.

## Start-of-Work Questions

- Do you want **strict** validation (fail on warnings) or **soft** validation (warn only)?
- Do you want **minimal** or **thorough** questioning?
- Decide L0/L5 via explicit trigger questions (see `references/interactive-questions.md`).

---

## L0 Problem Framing (Optional)

### Minimal
- What problem are we solving, in one sentence?
- Who are the primary stakeholders?
- What is explicitly out of scope?
- What would success look like in measurable terms?

### Thorough
- What are the top 3 goals and top 3 non-goals?
- Who owns the business outcomes, and what do they need?
- What constraints exist (budget, timeline, compliance, tech)?
- What assumptions are we making (and how confident are we)?
- What open questions must be answered before L1?
- What risks could invalidate the plan early?

---

## L1 Meta-Architecture

### Minimal
- What is the system’s purpose and primary users?
- What are the top 3–5 constraints (measurable)?
- What are the 3–5 guiding principles?
- What are success criteria (metrics)?

### Thorough
- What is the vision and impact (1–2 sentences)?
- List 5–7 constraints with measurable thresholds.
- List 3–5 principles and what decisions they guide.
- Define success criteria for latency, scale, reliability, and cost.
- What trade-offs are explicitly accepted?

---

## L2 System Architecture

### Minimal
- What are the major subsystems and their responsibilities?
- What data flows between them?
- What are the external interfaces?

### Thorough
- For each subsystem: what it owns, what it does not own.
- Data flow: sources, sinks, transformations, storage.
- Interfaces: protocol, auth, SLAs, rate limits.
- Which L1 constraints are addressed by which subsystems?
- Are there any boundary or ownership conflicts?
- Is there a migration plan (if legacy systems exist)?

---

## L3 Component Design

### Minimal
- What are the key modules and their APIs?
- What are the dependencies?
- What are the critical contracts?
- Populate `.plan/dependencies.yml` and mark `status: complete`.

### Thorough
- For each module: responsibilities, public API, config needs.
- Define API contracts with error handling.
- Dependency graph: ensure no cycles.
- Versioning strategy for APIs.
- Which L2 constraints map to L3 choices?

---

## L4 Implementation

### Minimal
- What is the file structure?
- What are the core patterns to follow?
- What validation commands will be used?

### Thorough
- File structure and module boundaries.
- Error handling, logging, and observability patterns.
- Testing strategy and build/deploy steps.
- Mapping of L3 contracts to implementation detail.
- Validation commands and expected outputs.

---

## L5 Operability & Readiness (Optional)

### Minimal
- What SLOs and alerting are required?
- What is the deployment/rollback strategy?
- What are the backup and recovery targets?

### Thorough
- SLOs, SLIs, measurement, and error budgets.
- Metrics/logs/traces/alerts coverage.
- Security controls and compliance checks.
- Deployment strategy and rollback triggers.
- RPO/RTO, backups, data retention.
- Cost guardrails and on-call/runbooks.
- Threat model and compliance evidence plan.

---

## PRD (Post-Architecture)

### Minimal
- What are the top 3 functional requirements?
- What are the top 3 non-functional requirements from the architecture?
- What is MVP scope and timeline?

### Thorough
- List functional requirements with IDs and acceptance criteria.
- List non-functional requirements mapped to L1/L5 constraints.
- Define user stories for each major workflow.
- Define success metrics and measurement plan.
- List risks, mitigations, and open questions.
