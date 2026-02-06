# PRD - Product Requirements (Post-Architecture)

Use this after L1–L4 (and L5 if applicable) are finalized. The PRD must align with the architecture decisions and constraints.

```yaml
product_name: "Project or system name"
version: "1.0"
architecture_sources:
- ".plan/L1-meta-architecture.md"
- ".plan/L2-system-architecture.md"
- ".plan/L3-component-design.md"
- ".plan/L4-implementation.md"
optional_architecture_sources:
- ".plan/L0-problem-framing.md"
- ".plan/L5-operability-readiness.md"
```

## 1. Summary
- Problem statement
- Target users
- One-sentence value proposition

## 2. Goals and Non-Goals
- Goals (aligned with L1 vision and success criteria)
- Non-goals (aligned with L0/L1 scope)

## 3. Requirements

### Functional Requirements
- FR-1: [Requirement]
- FR-2: [Requirement]

### Non-Functional Requirements
- NFR-1: [Constraint / SLO / SLA from L1/L5]
- NFR-2: [Constraint / SLO / SLA from L1/L5]

## 4. User Stories / Use Cases
- As a [user], I want [capability] so that [outcome].

## 5. Scope and Milestones
- MVP scope (aligned with architecture feasibility)
- Milestone plan

## 6. Dependencies
- External services
- Internal teams

## 7. Risks and Mitigations
- Risk: [Description] → Mitigation: [Action]

## 8. Success Metrics
- Metric: [Target]

## 9. Open Questions
- [Question]
