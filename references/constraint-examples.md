# Constraint Examples

This document provides comprehensive examples of constraints in layered architecture systems.

---

## 1. Constraint Types

### Performance
Constraints related to system speed and resource usage.

| Metric | Example Constraint | Measurement |
|--------|-------------------|-------------|
| Latency | "API response under 200ms at P99" | Response time |
| Throughput | "Process 10,000 requests/second" | Requests/time |
| Resources | "Memory usage under 2GB per instance" | Memory consumption |
| Bandwidth | "Transfer rate of 1Gbps sustained" | Data throughput |

### Security
Constraints ensuring system protection and compliance.

| Aspect | Example Constraint | Standard |
|--------|-------------------|----------|
| Authentication | "MFA required for admin access" | NIST 800-63 |
| Encryption | "TLS 1.3 for all data in transit" | PCI DSS |
| Compliance | "GDPR data retention policies" | GDPR |
| Audit | "All access logged with retention" | SOC 2 |

### Scalability
Constraints defining growth and load handling.

| Dimension | Example Constraint | Target |
|-----------|-------------------|--------|
| Users | "Support 100,000 concurrent users" | User count |
| Data | "Handle 1TB daily data ingestion" | Data volume |
| Growth | "Scale horizontally to 50 nodes" | Cluster size |
| Geography | "Deploy across 3 regions" | Distribution |

### Reliability
Constraints ensuring system availability and resilience.

| Factor | Example Constraint | Target |
|--------|-------------------|--------|
| Uptime | "99.99% availability (52min downtime/year)" | SLA |
| Fault Tolerance | "Zero single points of failure" | Architecture |
| Recovery | "RTO of 4 hours, RPO of 1 hour" | DR metrics |
| Durability | "99.9999999% data durability" | Data safety |

### Maintainability
Constraints ensuring long-term code health.

| Aspect | Example Constraint | Tool |
|--------|-------------------|------|
| Code Quality | "80% minimum code coverage" | Test runner |
| Documentation | "All public APIs documented" | Swagger/OpenAPI |
| Standards | "Follow organization style guide" | Linter |
| Debt | "No critical tech debt items >30 days" | Issue tracker |

---

## 2. Domain Examples

### Web Applications

**E-commerce Platform:**
- Performance: Page load under 2 seconds
- Security: PCI DSS compliance for payments
- Scalability: Handle Black Friday traffic (10x normal)
- Reliability: 99.9% uptime during business hours
- Maintainability: 90% test coverage on checkout flow

**Social Media Dashboard:**
- Performance: Real-time updates under 500ms
- Security: OAuth 2.0 with scoped permissions
- Scalability: Support 1M concurrent connections
- Reliability: Graceful degradation during spikes
- Maintainability: Component-based architecture

### API Services

**Payment Gateway API:**
```yaml
constraints:
  - id: API-PERF-001
    layer: L1
    text: "Process payment in under 500ms"
    type: performance
    priority: critical
  
  - id: API-SEC-001
    layer: L1
    text: "End-to-end encryption for all transactions"
    type: security
    standard: PCI-DSS
  
  - id: API-REL-001
    layer: L1
    text: "99.99% uptime with automatic failover"
    type: reliability
    sla: "99.99%"
```

**Analytics API:**
- Performance: Query response under 1 second
- Security: Row-level security per tenant
- Scalability: Process 1 billion events/day
- Reliability: Batch processing with checkpoint recovery
- Maintainability: OpenAPI spec with examples

### Database Systems

**Distributed Database:**
- Performance: Sub-10ms read latency
- Security: Encryption at rest and in transit
- Scalability: Automatic sharding beyond 10TB
- Reliability: Multi-region replication (3 copies)
- Maintainability: Automated backup and recovery

**Time-Series Database:**
- Performance: Ingest 1M metrics/second
- Security: Role-based access control
- Scalability: Retain 2 years of data
- Reliability: No data loss on node failure
- Maintainability: Automated data lifecycle management

### Microservices

**Order Service:**
```yaml
constraints:
  - id: MS-PERF-001
    layer: L1
    text: "Event processing latency under 100ms"
    type: performance
    validates_against: [MS-L2-event-handling]
  
  - id: MS-SCL-001
    layer: L1
    text: "Scale to 50 instances based on queue depth"
    type: scalability
    metric: "queue_depth > 1000"
  
  - id: MS-REL-001
    layer: L1
    text: "Circuit breaker trips after 5 consecutive failures"
    type: reliability
    pattern: "circuit-breaker"
```

---

## 3. Registry Format

### YAML Structure

The constraint registry uses a structured YAML format:

```yaml
# constraint-registry.yaml
version: "1.0"
project: "Example System"
last_updated: "2024-01-15"

constraints:
  # Level 1: Business/Domain Constraints
  - id: CON-001
    layer: L1
    text: "Support 10,000 concurrent users"
    type: performance
    category: scalability
    priority: critical
    validates_against: [L2-capacity-planning, L2-load-balancing]
    owner: "Product Team"
    created: "2024-01-01"
  
  - id: CON-002
    layer: L1
    text: "Comply with GDPR data protection requirements"
    type: security
    category: compliance
    priority: critical
    standard: "GDPR"
    validates_against: [L2-data-encryption, L2-access-control, L2-audit-logging]
    owner: "Compliance Team"
    created: "2024-01-01"
  
  - id: CON-003
    layer: L1
    text: "99.99% uptime during business hours (8am-6pm)"
    type: reliability
    category: availability
    priority: high
    sla: "99.99%"
    validates_against: [L2-redundancy, L2-monitoring, L2-failover]
    owner: "Operations Team"
    created: "2024-01-01"
  
  # Level 2: Architecture Constraints
  - id: L2-capacity-planning
    layer: L2
    text: "Auto-scaling between 5-20 instances"
    type: scalability
    derived_from: CON-001
    implementation: "Kubernetes HPA"
  
  - id: L2-load-balancing
    layer: L2
    text: "Distribute load across availability zones"
    type: reliability
    derived_from: CON-001
    implementation: "AWS ALB with health checks"
  
  - id: L2-data-encryption
    layer: L2
    text: "AES-256 encryption for data at rest"
    type: security
    derived_from: CON-002
    implementation: "Database TDE + application encryption"
  
  # Level 3: Implementation Constraints
  - id: L3-query-optimization
    layer: L3
    text: "All database queries under 50ms"
    type: performance
    derived_from: L2-capacity-planning
    enforced_by: "Query timeout + monitoring"
    
  - id: L3-connection-pooling
    layer: L3
    text: "Database connection pool: min 10, max 100"
    type: performance
    derived_from: L2-capacity-planning
    enforced_by: "HikariCP configuration"
```

### Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `id` | Yes | Unique identifier | `CON-001` |
| `layer` | Yes | Architecture layer (L1/L2/L3) | `L1` |
| `text` | Yes | Human-readable constraint | `"Support 10,000 concurrent users"` |
| `type` | Yes | Constraint category | `performance` |
| `priority` | No | Criticality level | `critical`, `high`, `medium`, `low` |
| `validates_against` | No | Downstream constraints this validates | `[L2-capacity, L2-load-balancer]` |
| `derived_from` | No | Upstream constraint this implements | `CON-001` |
| `owner` | No | Team responsible | `Product Team` |
| `implementation` | No | How constraint is implemented | `Kubernetes HPA` |
| `enforced_by` | No | Enforcement mechanism | `Lint rule, Runtime check` |

---

## 4. Propagation Examples

### Example 1: Performance Constraint Flow

**Business Requirement (L1):**
```yaml
- id: PERF-001
  layer: L1
  text: "Page load time under 2 seconds for 95th percentile"
  type: performance
```

**Architecture Decisions (L2):**
```yaml
- id: L2-PERF-001a
  layer: L2
  text: "CDN for static assets with edge caching"
  derived_from: PERF-001
  
- id: L2-PERF-001b
  layer: L2
  text: "API response caching with 5-minute TTL"
  derived_from: PERF-001
  
- id: L2-PERF-001c
  layer: L2
  text: "Database read replicas for query distribution"
  derived_from: PERF-001
```

**Implementation (L3):**
```yaml
- id: L3-PERF-001a
  layer: L3
  text: "CloudFront distribution with 24-hour static asset caching"
  derived_from: L2-PERF-001a
  
- id: L3-PERF-001b
  layer: L3
  text: "Redis cache layer with cache-aside pattern"
  derived_from: L2-PERF-001b
  
- id: L3-PERF-001c
  layer: L3
  text: "Query timeout of 1000ms with statement timeout"
  derived_from: L2-PERF-001c
```

**Flow Diagram:**
```
L1: Page load < 2s (95th percentile)
    │
    ├──→ L2: CDN for static assets
    │         └──→ L3: CloudFront + 24h cache
    │
    ├──→ L2: API caching (5min TTL)
    │         └──→ L3: Redis cache-aside
    │
    └──→ L2: DB read replicas
              └──→ L3: 1000ms query timeout
```

### Example 2: Security Constraint Flow

**Business Requirement (L1):**
```yaml
- id: SEC-001
  layer: L1
  text: "All sensitive data encrypted at rest and in transit"
  type: security
  compliance: [SOC2, PCI-DSS]
```

**Architecture Decisions (L2):**
```yaml
- id: L2-SEC-001a
  layer: L2
  text: "TLS 1.3 mandatory for all service communication"
  derived_from: SEC-001
  
- id: L2-SEC-001b
  layer: L2
  text: "Database Transparent Data Encryption (TDE)"
  derived_from: SEC-001
  
- id: L2-SEC-001c
  layer: L2
  text: "Application-level encryption for PII fields"
  derived_from: SEC-001
```

**Implementation (L3):**
```yaml
- id: L3-SEC-001a
  layer: L3
  text: "Envoy proxy with TLS 1.3 enforcement"
  derived_from: L2-SEC-001a
  
- id: L3-SEC-001b
  layer: L3
  text: "AWS RDS with TDE enabled"
  derived_from: L2-SEC-001b
  
- id: L3-SEC-001c
  layer: L3
  text: "AES-256-GCM field encryption using AWS KMS"
  derived_from: L2-SEC-001c
```

### Example 3: Reliability Constraint Flow

**Business Requirement (L1):**
```yaml
- id: REL-001
  layer: L1
  text: "Zero data loss during regional outage"
  type: reliability
  sla: "RPO = 0"
```

**Propagation Chain:**
```
L1: Zero data loss in regional outage
    │
    ├──→ L2: Synchronous replication across regions
    │         └──→ L3: PostgreSQL synchronous_commit = remote_apply
    │         └──→ L3: Application-level write acknowledgment
    │
    ├──→ L2: Multi-region active-active deployment
    │         └──→ L3: Global load balancer with health checks
    │         └──→ L3: Conflict-free replicated data types (CRDTs)
    │
    └──→ L2: Automated failover under 30 seconds
              └──→ L3: Kubernetes operator with pod disruption budgets
              └──→ L3: Circuit breaker pattern in service mesh
```

---

## 5. Anti-Patterns

### Vague Constraints

❌ **Bad:** "The system should be fast"

✅ **Good:** "API p95 response time under 200ms at 1000 requests/second"

**Why:** "Fast" is subjective. Concrete metrics enable measurement and validation.

---

❌ **Bad:** "Support many users"

✅ **Good:** "Support 10,000 concurrent users with 5% annual growth"

**Why:** Quantify "many" and consider future growth.

---

❌ **Bad:** "Good security"

✅ **Good:** "Implement OWASP Top 10 mitigations and pass annual penetration test"

**Why:** Reference standards and include validation method.

---

### Conflicting Constraints

❌ **Bad Pair:**
```yaml
- "Keep the architecture simple"
- "Support 50 microservices with complex orchestration"
```

**Resolution:** Prioritize and document trade-offs:
```yaml
primary_constraint: "Support 50 microservices"
trade_off: "Accept increased operational complexity"
rationale: "Business scaling requirements outweigh simplicity"
```

---

❌ **Bad Pair:**
```yaml
- "Minimize infrastructure cost"
- "99.999% uptime SLA"
```

**Resolution:** Define budget and alternatives:
```yaml
uptime_target: "99.99%"
budget_limit: "$50,000/month"
alternative: "Graceful degradation during cost spikes"
```

---

### Too Many Constraints

❌ **Anti-Pattern:** Listing 15+ constraints without prioritization

**Problem:** Teams cannot focus. Constraints will inevitably conflict.

✅ **Better Approach:**
```yaml
tier_1_critical:  # Max 3-5
  - "99.99% uptime"
  - "PCI DSS compliance"
  - "Sub-200ms response time"
  
tier_2_important:  # Max 5-7
  - "SOC 2 Type II compliance"
  - "Horizontal scaling to 50 nodes"
  
tier_3_nice_to_have:  # Unlimited
  - "Dark mode UI"
  - "Keyboard shortcuts"
```

---

### Unmeasurable Constraints

❌ **Bad:** "Provide good UX"

**Problems:**
- No objective measurement
- Cannot validate implementation
- Subjective interpretation

✅ **Good:**
```yaml
- id: UX-001
  layer: L1
  text: "Complete checkout in under 3 clicks from cart"
  type: usability
  measurement: "User testing with 20 participants, 90% completion rate"
  
- id: UX-002
  layer: L1
  text: "NPS score above 50 within 6 months of launch"
  type: satisfaction
  measurement: "Quarterly customer surveys"
  
- id: UX-003
  layer: L1
  text: "Task completion rate above 85% for core workflows"
  type: usability
  measurement: "Analytics tracking + usability testing"
```

---

❌ **Bad:** "Code should be maintainable"

✅ **Good:**
```yaml
- id: MAINT-001
  layer: L1
  text: "Mean time to fix critical bugs under 4 hours"
  type: maintainability
  measurement: "Issue tracker metrics"
  
- id: MAINT-002
  layer: L1
  text: "New developer can onboard and deploy in under 3 days"
  type: maintainability
  measurement: "Onboarding time tracking"
  
- id: MAINT-003
  layer: L2
  text: "Cyclomatic complexity under 10 per function"
  type: maintainability
  measurement: "Static analysis (SonarQube)"
```

---

## Summary

Effective constraints are:
- **Specific:** Quantify targets (numbers, percentages, time)
- **Measurable:** Include how to validate
- **Achievable:** Realistic given resources
- **Relevant:** Directly tied to business needs
- **Time-bound:** Include deadlines or review periods
- **Prioritized:** Rank by importance
- **Consistent:** No conflicts without documented trade-offs

Use the YAML registry format to track constraints across all three layers (L1/L2/L3), ensuring traceability from business requirements through implementation details.
