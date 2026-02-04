# Validation Gate Criteria

Criteria for validating transitions between architecture layers.

---

## Optional Layer Triggers

L0 and L5 are **optional** and should only be used when specific triggers apply.

See the templates for these layers:
- `assets/template-l0-problem-framing.md`
- `assets/template-l5-operability-readiness.md`

### L0 Trigger Rules (Problem Framing)
- Requirements are unclear or contradictory
- Stakeholder goals are in conflict
- Scope boundaries are undefined or shifting
- Success criteria are not yet measurable
- Known unknowns are blocking architecture decisions

If none of the above apply, skip L0 and record a brief skip reason.

### L5 Trigger Rules (Operability & Readiness)
- System is nearing delivery or implementation
- Reliability, security, or compliance are high-stakes
- Cost controls or production guardrails are required
- Operational readiness must be verified explicitly

If none of the above apply, skip L5 and record a brief skip reason.

---

## Gate L0→L1 Criteria (Optional)

Validation gates for transitioning from Problem Framing (L0) to Meta-Architecture (L1):

### 0.1 Goals and Non-Goals Are Explicit
- Goals are clear and concise
- Non-goals prevent scope creep
- Each goal is traceable to a stakeholder need

### 0.2 Stakeholders and Needs Are Captured
- Key stakeholders are listed
- Each stakeholder has a concrete need
- No critical stakeholder class is missing

### 0.3 Assumptions and Open Questions Are Listed
- Assumptions have confidence levels
- Open questions are actionable
- Any blocking question is flagged

### 0.4 Draft Success Criteria Are Present
- Measurable targets are proposed
- Criteria can be refined at L1 without re-scoping

### 0.5 Decision Readiness Is Declared
- Mark "ready" only when L1 can proceed without guessing
- Otherwise, remain "not_ready" and resolve open questions

---

## Gate L1→L2 Criteria

Validation gates for transitioning from Vision (L1) to System Definition (L2):

### 1.1 Constraints Are Specific and Testable
- Each constraint must have a clear pass/fail condition
- Avoid vague language like "good performance" or "user-friendly"
- Constraints must be verifiable through testing or inspection
- Include quantifiable metrics where possible

### 1.2 Principles Are Actionable
- Every principle must translate to a concrete decision
- Principles should guide trade-off decisions
- Must be applicable at design and implementation time
- Avoid platitudes that cannot guide actual work

### 1.3 Success Criteria Have Measurable Targets
- Define specific metrics with thresholds
- Include acceptance criteria for each success dimension
- Targets must be realistic yet ambitious
- Success criteria must be observable and verifiable

### 1.4 No Circular Dependencies in Vision
- Vision goals must not create dependency cycles
- Each goal should stand independently or depend on completed goals
- Circular references between objectives indicate unclear thinking
- Dependencies must flow from core to derived goals

### 1.5 Constraint Count ≤ 7
- Limit architectural constraints to at most 7 items
- Excessive constraints indicate unfocused scope
- Each constraint must be essential to the vision
- Fewer, stronger constraints beat many weak ones

---

## Gate L2→L3 Criteria

Validation gates for transitioning from System Definition (L2) to Component Design (L3):

### 2.1 System Boundaries Are Closed Under Operations
- All system operations must stay within defined boundaries
- No undefined interfaces crossing boundary lines
- Boundary violations must be resolved before proceeding
- Operations must be complete, not partial

### 2.2 All Interfaces Have Defined Contracts
- Every interface must specify inputs, outputs, and behaviors
- Contracts must include error conditions and edge cases
- Pre-conditions and post-conditions must be documented
- Interface contracts must be verifiable

### 2.3 Data Flow Is Complete (No Orphaned Data)
- All data must have a clear producer and consumer
- No data elements without defined sources or destinations
- Data lifecycle must be fully specified
- Temporary or intermediate data must be accounted for

### 2.4 Constraints from L1 Are Addressed
- Every L1 constraint must be satisfied by L2 design
- No constraint should be ignored or violated
- Design choices must reference specific constraints
- Trade-offs must document which constraints they serve

### 2.5 Subsystem Responsibilities Are Clear
- Each subsystem must have a single, clear responsibility
- No overlapping responsibilities between subsystems
- Every subsystem must contribute to overall system goals
- Subsystem boundaries must minimize coupling

---

## Gate L3→L4 Criteria

Validation gates for transitioning from Component Design (L3) to Implementation (L4):

### 3.1 All Interfaces Have Concrete Signatures
- All interfaces must have language-specific signatures
- Type information must be fully specified
- Parameter names and meanings must be documented
- Return types and error conditions must be explicit

### 3.2 Dependencies Form DAG (No Cycles)
- Component dependency graph must be acyclic
- Circular dependencies indicate design flaw
- Dependencies must flow from stable to less stable components
- Use dependency inversion where cycles would otherwise form

### 3.3 Component Contracts Are Implementable
- All contracts must be implementable with available technology
- Contracts must not violate physical or logical constraints
- Performance requirements in contracts must be achievable
- Error conditions must be handleable by calling code

### 3.4 No Constraint Violations from L1/L2
- L4 implementation must respect all L1 and L2 constraints
- Any discovered violation must be documented and escalated
- Implementation choices must trace back to design decisions
- Violations require gate rejection and design revision

---

## Gate L4→L5 Criteria (Optional)

Validation gates for transitioning from Implementation (L4) to Operability & Readiness (L5):

### 4.1 SLOs and SLI Measurements Are Defined
- SLOs include explicit targets and measurement method
- SLI definitions map to actual telemetry sources

### 4.2 Observability Is End-to-End
- Metrics, logs, traces, and alerts are defined
- Alerts include severity and trigger conditions

### 4.3 Security Controls Are Listed and Mapped
- Controls address identified risks and constraints
- Compliance requirements are referenced if applicable

### 4.4 Deployment and Rollback Are Safe
- Deployment strategy is explicit
- Rollback criteria and steps are documented

### 4.5 Data Protection Is Defined
- Backups, retention, RPO, and RTO are explicit
- Dependencies on storage providers are known

### 4.6 Readiness Checks Are Actionable
- Checks are verifiable and testable
- Readiness status is declared ("ready" or "not_ready")

---

## Soft Gate Behavior

Soft gates issue warnings but allow proceeding. Use soft gates for:

### 4.1 Warnings Not Errors
- Non-blocking issues that should be addressed
- Areas that need attention but not rework
- Optional improvements or optimizations
- Documentation gaps that don't affect correctness

### 4.2 Can Proceed Anyway
- Progress is not blocked by soft gate warnings
- Team decides whether to address or proceed
- Warnings do not prevent gate passing
- May require sign-off to acknowledge warnings

### 4.3 Issues Logged for Review
- All soft gate warnings are logged
- Issues are tracked for later resolution
- Review periodically for accumulation
- May become hard gates in future iterations

### 4.4 Categories

#### CRITICAL
- Likely to cause system failure
- Security vulnerabilities
- Data integrity risks
- Performance degradation
- Must be addressed before production

#### WARNING
- May cause issues in edge cases
- Technical debt that will accumulate
- Maintenance difficulties
- Should be addressed in current iteration

#### INFO
- Suggestions for improvement
- Opportunities for optimization
- Best practice recommendations
- Can be deferred indefinitely

---

## Escalation Paths

Procedures for when L4 reveals the need to change L2:

### 5.1 When L4 Reveals Need to Change L2
- Implementation discovers fundamental design flaw
- Requirements were misunderstood or incomplete
- Technical constraints were unknown during design
- Performance or scalability issues emerge

### 5.2 Document Issue
- Record the problem discovered at L4
- Explain why L2 design cannot accommodate the issue
- Specify which L2 elements need modification
- Estimate impact of changes on downstream work

### 5.3 Checkpoint Current State
- Save current L4 implementation state
- Tag or branch version control
- Document what work will be affected
- Identify what can be salvaged vs. must be discarded

### 5.4 Return to L2, Update, Propagate
1. **Return**: Roll back to L2 system definition
2. **Update**: Modify L2 design to address the issue
3. **Propagate**: Push changes forward through L3 and L4
4. **Verify**: Re-run all gates with updated design
5. **Resume**: Continue implementation with corrected design

### Escalation Decision Tree

```
L4 Issue Discovered
        │
        ▼
┌─────────────────────┐
│ Can fix in L4 only? │
└─────────────────────┘
        │
    ┌───┴───┐
    ▼       ▼
   YES      NO
    │       │
    ▼       ▼
┌────────┐ ┌──────────────────┐
│ Fix    │ │ Document Issue   │
│ in L4  │ │ Checkpoint State │
└────────┘ │ Return to L2     │
           │ Update L2        │
           │ Propagate        │
           └──────────────────┘
```

---

## Summary

| Gate     | Focus              | Failure Action          |
|----------|-------------------|------------------------|
| L0 → L1  | Problem clarity   | Resolve unknowns        |
| L1 → L2  | Vision clarity    | Refine vision          |
| L2 → L3  | System boundaries | Adjust system design   |
| L3 → L4  | Component design  | Redesign components    |
| L4 → L5  | Operability       | Complete readiness gaps|
| L4 Issue | Implementation    | Escalate to L2 if needed|

Validation gates ensure quality at each layer while providing clear paths for handling discovered issues.
