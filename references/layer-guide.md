# Layered Architecture Guide

A comprehensive guide for designing and implementing software systems using a 4-layer architecture approach.

---

## Optional Layers (L0/L5)

L0 and L5 are optional and should only be used when their triggers apply to avoid bloat.

### L0: Problem Framing (Optional)

**Use when:** requirements are unclear, scope is fuzzy, or goals conflict.

**L0 Template (YAML):**
```yaml
layer: L0
title: "Project or system name"
triggered_by: "Why L0 was needed"
goals:
- "Primary goal"
non_goals:
- "Explicitly out of scope"
stakeholders:
- role: "Role or team"
  needs: "What they need from this system"
assumptions:
- text: "Assumption statement"
  confidence: medium
open_questions:
- "Question that must be resolved before L1"
success_criteria_draft:
- "Measurable or verifiable outcome"
decision_readiness: not_ready
notes: ""
```

#### Risk Register (Required when L5 is used)
Top risks with severity and mitigation:
1. **Risk**: [Description]
   - **Severity**: Low/Medium/High
   - **Mitigation**: [Action]
   - **Owner**: [Role/Team]

### L5: Operability & Readiness (Optional)

**Use when:** moving toward delivery or when reliability, security, or cost require explicit readiness checks.

**L5 Template (YAML):**
```yaml
layer: L5
title: "Project or system name"
slos:
- name: "Availability"
  sli: "Successful requests / total requests"
  target: "99.9% monthly"
  measurement: "APM dashboard"
observability:
  metrics:
  - "Request rate, error rate, latency"
  logs:
  - "Structured request logs with trace_id"
  traces:
  - "Distributed tracing across all services"
  alerting:
  - "P1 for sustained error rate > X"
security_controls:
- "TLS 1.3 everywhere"
deployment:
  strategy: "Blue/green with automatic rollback"
  rollback: "Revert on error budget burn or failed health checks"
  environments:
  - "dev"
  - "staging"
  - "prod"
data_protection:
  backups: "Daily backups with point-in-time recovery"
  retention: "90 days"
  rpo: "15 minutes"
  rto: "1 hour"
cost_guardrails:
- "Monthly budget cap $X"
runbooks:
- "Incident response runbook"
readiness_checks:
- "Load test meets SLOs"
readiness_status: not_ready
residual_risks:
- "Known risk not yet mitigated"
dependencies:
- "External service or vendor dependency"
notes: ""
```

### Optional Flow

1. If L0 triggers apply, complete L0, then proceed to L1.
2. Proceed through L1 → L4 as usual.
3. If L5 triggers apply, complete L5 after L4.
4. If L0/L5 are skipped, record a brief skip reason.

---

## L1: Meta-Architecture

### Purpose
Define the vision, constraints, principles, and success criteria that guide all architectural decisions.

### Definition of Done (L1)
- Vision is 1–2 sentences and names primary users
- 3–7 measurable constraints with thresholds
- 3–5 actionable principles
- Success criteria expressed as metrics
- Decision log and risk register populated with at least 1 item each

### Required Sections

#### Vision
- What problem does this system solve?
- Who are the users?
- What is the desired impact?

#### Constraints (5-7 max)
Hard limits that shape the architecture:
1. **Budget**: Maximum cost per month/year
2. **Timeline**: Delivery deadlines
3. **Compliance**: Regulatory requirements (GDPR, HIPAA, etc.)
4. **Technology**: Approved/legacy technologies
5. **Scale**: Expected user load, data volume
6. **Team**: Available skills and headcount
7. **External**: Vendor lock-in, integration requirements

#### Principles (3-5)
Guiding values for decision-making:
1. **Simplicity**: Prefer simple solutions over clever ones
2. **Modularity**: Design for change and replaceability
3. **Observability**: Everything must be measurable
4. **Security by Design**: Defense in depth at every layer
5. **Performance**: Define SLAs upfront

#### Success Criteria
Measurable targets:
- Availability: 99.9% uptime
- Latency: P95 < 200ms
- Throughput: 10,000 RPS
- Time to recovery: < 1 hour
- Code coverage: > 80%

#### Decision Log (Required)
Key decisions and rationale:
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]

#### Risk Register (Required)
Top risks with severity and mitigation:
1. **Risk**: [Description]
   - **Severity**: Low/Medium/High
   - **Mitigation**: [Action]
   - **Owner**: [Role/Team]

### Limits
- Maximum 7 constraints
- Maximum 5 principles
- All success criteria must be measurable

### L1 Example

```markdown
## L1: Payment Platform Meta-Architecture

### Vision
Enable instant, secure payment processing for e-commerce merchants
with sub-second transaction completion.

### Constraints
1. PCI-DSS Level 1 compliance required
2. Maximum 6-month delivery timeline
3. Support 100K concurrent transactions
4. Must integrate with 3 major payment processors
5. Zero-downtime deployments
6. AWS infrastructure only
7. Team of 8 engineers

### Principles
1. **Security First**: All data encrypted at rest and in transit
2. **Fault Tolerance**: No single point of failure
3. **Auditability**: Every transaction fully traceable

### Success Criteria
- 99.99% transaction success rate
- P99 latency < 500ms for authorization
- Zero data breaches
- < 5 minute MTTR
- Support 50% YoY growth
```

---

## L2: System Architecture

### Purpose
Define the high-level system structure: subsystems, boundaries, and data flow between them.

### Definition of Done (L2)
- Subsystems listed with clear ownership
- Boundaries declared (inside vs outside)
- Data flow described end-to-end
- Interfaces list protocol + auth + SLAs where applicable
- Migration strategy present if legacy systems exist
- Tradeoff matrix filled for at least 1 key decision
- Decision log has at least 1 entry

### Required Sections

#### Subsystem Inventory
List all major subsystems with:
- Name and purpose
- Owner/team
- Criticality (critical/high/medium/low)
- Lifecycle stage (new/maturing/legacy/deprecated)

#### Boundary Definitions
For each subsystem:
- What it owns (data, functionality)
- What it doesn't own
- Dependencies on other subsystems
- Public interface surface

#### Data Flow
- External inputs and outputs
- Inter-subsystem communication patterns
- Data transformation points
- State persistence locations

#### Interfaces
Contract summaries:
- Protocol (REST, gRPC, message queue, etc.)
- Authentication method
- Rate limits
- SLAs

#### Migration Strategy (Required when legacy systems exist)
- Phased plan (strangler, parallel run, cutover)
- Data migration approach
- Rollback strategy

#### Tradeoff Matrix (Required)
At least two options:
1. **Option A**: [Approach]
   - **Pros**: [List]
   - **Cons**: [List]
2. **Option B**: [Approach]
   - **Pros**: [List]
   - **Cons**: [List]
**Decision**: [Chosen option + rationale]

#### Decision Log (Required)
Key decisions and rationale:
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]

### Limits
- All interfaces must have contracts defined
- No circular dependencies between subsystems
- Each subsystem must have clear ownership

### L2 Example

```markdown
## L2: Payment Platform System Architecture

### Subsystem Inventory
1. **Payment Gateway** (Team A, Critical, New)
   - Handles incoming payment requests
   
2. **Fraud Detection** (Team B, Critical, New)
   - Real-time risk scoring
   
3. **Transaction Processor** (Team A, Critical, New)
   - Executes payments
   
4. **Ledger Service** (Team C, Critical, New)
   - Records all transactions
   
5. **Notification Service** (Team D, High, Maturing)
   - Sends receipts and alerts

### Boundary Definitions

**Payment Gateway**
- Owns: Request validation, routing
- Doesn't own: Payment execution, storage
- Depends on: Fraud Detection, Transaction Processor
- Interface: REST API (public), gRPC (internal)

**Transaction Processor**
- Owns: Payment execution logic
- Doesn't own: Request handling, notifications
- Depends on: Ledger Service, external processors
- Interface: gRPC, message queue

### Data Flow
```
Client → Payment Gateway → Fraud Detection
                              ↓
Client ← Response ← Transaction Processor
                         ↓
                    Ledger Service
                         ↓
                    Notification Service
```

### Interfaces

**Payment Gateway → Fraud Detection**
- Protocol: gRPC
- Auth: mTLS
- Rate limit: 10K RPS
- SLA: P95 < 50ms

**Transaction Processor → Ledger Service**
- Protocol: Message queue (Kafka)
- Auth: SASL/SSL
- SLA: At-least-once delivery
```

---

## L3: Component Design

### Purpose
Define the internal structure of subsystems: modules, APIs, and dependencies.

### Definition of Done (L3)
- Modules enumerated with responsibilities
- API contracts include inputs, outputs, and errors
- Dependency graph is acyclic
- Decision log has at least 1 entry

### Required Sections

#### Module Specifications
For each module within a subsystem:
- Responsibilities
- Public API surface
- Internal structure
- Configuration requirements

#### API Contracts
Detailed interface specifications:
- Endpoint/operation definitions
- Request/response schemas
- Error codes and handling
- Versioning strategy

#### Dependency Graph
- Internal module dependencies
- External service dependencies
- Library/framework dependencies
- Version constraints

#### Decision Log (Required)
Key decisions and rationale:
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]

### Limits
- All public interfaces need type signatures
- No module should have > 7 dependencies
- API versions must be explicit

### L3 Example

```markdown
## L3: Payment Gateway Component Design

### Module Specifications

#### Validation Module
- **Responsibilities**: Schema validation, field sanitization
- **Public API**:
  ```typescript
  interface Validator {
    validate(request: PaymentRequest): ValidationResult;
    sanitize(input: unknown): SanitizedPaymentRequest;
  }
  ```
- **Config**: `VALIDATION_STRICT_MODE`, `MAX_AMOUNT_LIMIT`

#### Routing Module
- **Responsibilities**: Route to appropriate processor
- **Public API**:
  ```typescript
  interface Router {
    route(request: PaymentRequest): ProcessorConfig;
    getFallback(processor: string): ProcessorConfig;
  }
  ```
- **Config**: `ROUTING_RULES`, `FALLBACK_ENABLED`

#### Auth Module
- **Responsibilities**: API key validation, merchant lookup
- **Public API**:
  ```typescript
  interface AuthService {
    authenticate(credentials: ApiCredentials): MerchantContext;
    authorize(merchant: string, operation: string): boolean;
  }
  ```

### API Contracts

**POST /v1/payments**
```typescript
// Request
interface PaymentRequest {
  merchant_id: string;
  amount: number;        // in cents
  currency: string;      // ISO 4217
  payment_method: CardDetails | BankDetails;
  idempotency_key: string;
}

// Response (200)
interface PaymentResponse {
  transaction_id: string;
  status: 'authorized' | 'declined' | 'pending';
  timestamp: string;
  processor_response: ProcessorResponse;
}

// Errors
400 - Invalid request schema
401 - Authentication failed
402 - Payment declined
429 - Rate limit exceeded
500 - Internal server error
```

### Dependency Graph
```
payment-gateway/
├── validation/
│   └── joi@17.x
├── routing/
│   └── config-service (L2)
├── auth/
│   └── redis@7.x
└── handlers/
    ├── validation
    ├── auth
    └── routing
```
```

---

## L4: Implementation

### Purpose
Define concrete code structure, patterns, and implementation details.

### Definition of Done (L4)
- File structure is explicit (paths and module boundaries)
- Code patterns are listed with rationale
- Testing strategy and validation commands defined
- Build/deploy steps summarized
- Decision log has at least 1 entry
- No full code implementations required; use patterns and stubs only

### Required Sections

#### File Structure
Directory layout with file purposes:
```
src/
├── modules/
│   ├── validation/
│   │   ├── index.ts          # Public exports
│   │   ├── validator.ts      # Core logic
│   │   ├── schemas.ts        # Joi schemas
│   │   └── tests/
│   │       └── validator.test.ts
│   └── ...
├── shared/
│   ├── types/                # Global type definitions
│   ├── errors/               # Error classes
│   └── utils/                # Utilities
├── config/
│   └── default.yaml
└── app.ts                    # Entry point
```

#### Code Patterns
Standard implementations:
- Error handling pattern
- Logging pattern
- Database access pattern
- API response pattern
- Testing pattern

#### Implementation Details
Specific code examples:
- Core classes/functions
- Configuration loading
- Middleware setup
- Error handling
- Observability integration

#### Decision Log (Required)
Key decisions and rationale:
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]

### Limits
- Concrete file paths required
- Patterns must be consistent
- All error cases handled

### L4 Example

```markdown
## L4: Payment Gateway Implementation

### File Structure
```
src/
├── modules/
│   ├── validation/
│   │   ├── index.ts
│   │   ├── validator.ts
│   │   ├── schemas.ts
│   │   └── tests/
│   │       └── validator.test.ts
│   ├── routing/
│   │   ├── index.ts
│   │   ├── router.ts
│   │   └── tests/
│   │       └── router.test.ts
│   └── auth/
│       ├── index.ts
│       ├── auth-service.ts
│       └── tests/
│           └── auth.test.ts
├── shared/
│   ├── types/
│   │   ├── payment.ts
│   │   └── errors.ts
│   ├── errors/
│   │   ├── index.ts
│   │   ├── payment-error.ts
│   │   └── validation-error.ts
│   └── utils/
│       ├── logger.ts
│       └── metrics.ts
├── middleware/
│   ├── error-handler.ts
│   ├── auth-middleware.ts
│   └── request-logger.ts
├── config/
│   └── default.yaml
├── app.ts
└── server.ts
```

### Code Patterns

#### Error Handling
```typescript
// shared/errors/payment-error.ts
export class PaymentError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number,
    public retryable: boolean = false
  ) {
    super(message);
  }
}

// Usage
throw new PaymentError(
  'INSUFFICIENT_FUNDS',
  'Card declined: insufficient funds',
  402,
  false
);
```

#### Validation Pattern
```typescript
// modules/validation/validator.ts
import Joi from 'joi';
import { PaymentRequest } from '../../shared/types/payment';

const paymentSchema = Joi.object({
  merchant_id: Joi.string().uuid().required(),
  amount: Joi.number().positive().required(),
  currency: Joi.string().length(3).required(),
  // ...
});

export function validate(request: unknown): PaymentRequest {
  const { error, value } = paymentSchema.validate(request);
  if (error) {
    throw new ValidationError('INVALID_REQUEST', error.message);
  }
  return value;
}
```

#### API Route Pattern
```typescript
// modules/payment/routes.ts
import { Router } from 'express';
import { validate } from '../validation';
import { authMiddleware } from '../../middleware/auth-middleware';
import { asyncHandler } from '../../shared/utils/async-handler';

const router = Router();

router.post(
  '/v1/payments',
  authMiddleware,
  asyncHandler(async (req, res) => {
    const request = validate(req.body);
    const result = await paymentService.process(request);
    res.status(200).json(result);
  })
);
```

### Implementation Details

#### Entry Point (app.ts)
```typescript
import express from 'express';
import { errorHandler } from './middleware/error-handler';
import { requestLogger } from './middleware/request-logger';
import { paymentRoutes } from './modules/payment/routes';
import { metrics } from './shared/utils/metrics';

const app = express();

app.use(express.json());
app.use(requestLogger);
app.use(metrics.middleware);

app.use('/v1/payments', paymentRoutes);

app.use(errorHandler);

export { app };
```

#### Configuration Loading
```typescript
// config/config.ts
import yaml from 'js-yaml';
import { readFileSync } from 'fs';

const config = yaml.load(
  readFileSync('./config/default.yaml', 'utf8')
) as Config;

export { config };
```
```

---

## Layer Isolation Protocol

### Principle
Each layer should only have visibility into:
1. The current layer's full detail
2. The parent layer's summary

### Rules

**Never Load Full Architecture**
- L4 doesn't read full L3 documentation
- L3 doesn't read full L2 documentation
- Each layer works from parent summaries only

**Cross-Layer Communication**
- Happens only through defined summaries
- No direct dependency on implementation details
- Changes in child layers don't affect parents

**Summary-Driven Development**
- Parent layers provide constraint summaries
- Child layers implement within those constraints
- Bidirectional communication through formal review process

### Benefits
1. **Reduced Cognitive Load**: Only relevant details visible
2. **Independent Evolution**: Layers change independently
3. **Parallel Development**: Teams work on different layers simultaneously
4. **Clear Contracts**: Summaries enforce boundaries

---

## Summary Format

### Purpose
Provide just enough context for child/parent layers to work effectively.

### Template

```markdown
## [Layer N] Summary: [System/Component Name]

### Context from Parent
[Key constraints, interfaces, and expectations from parent layer]

### Scope
[What this layer owns and is responsible for]

### Key Decisions
1. [Decision 1 - brief rationale]
2. [Decision 2 - brief rationale]
3. ...

### Interfaces
**Provides:**
- [Interface 1: format, SLA]
- [Interface 2: format, SLA]

**Requires:**
- [Dependency 1: interface, SLA]
- [Dependency 2: interface, SLA]

### Constraints Imposed on Children
- [Constraint 1]
- [Constraint 2]

### Open Questions
- [Question 1]
- [Question 2]
```

### Example: L2 Summary for L3

```markdown
## L2 Summary: Payment Gateway

### Context from L1
- Must achieve P95 < 500ms for auth
- PCI-DSS compliance required
- Target: 100K concurrent transactions

### Scope
Payment Gateway subsystem handles:
- Request validation
- Merchant authentication
- Payment routing
- Response formatting

**Out of scope**: Payment execution, ledger recording, fraud detection

### Key Decisions
1. **Protocol**: REST for public API, gRPC for internal
2. **Auth**: API keys with HMAC-SHA256 signatures
3. **Rate Limiting**: Token bucket per merchant

### Interfaces
**Provides:**
- POST /v1/payments (JSON, P95 < 200ms)
- POST /v1/refunds (JSON, P95 < 300ms)

**Requires:**
- Fraud Detection: gRPC, P95 < 50ms
- Transaction Processor: message queue, async

### Constraints Imposed on L3
- All endpoints must validate merchant context
- Every request logged with trace ID
- Circuit breaker pattern for downstream calls

### Open Questions
- [None - ready for L3 design]
```

---

## Quick Reference

### When to Use Each Layer

| Situation | Start At | Deliverable |
|-----------|----------|-------------|
| New project | L1 | Architecture decision record |
| New subsystem | L2 | Subsystem design doc |
| New module | L3 | Module API spec |
| New feature | L4 | Implementation PR |

### Review Checkpoints

- **L1 → L2**: Do constraints enable the vision?
- **L2 → L3**: Do boundaries support the flow?
- **L3 → L4**: Do APIs enable clean implementation?
- **L4 → Review**: Does code follow patterns?

### Common Pitfalls

1. **Over-constraining L1**: Too many constraints stifle design
2. **Unclear boundaries in L2**: Leads to tight coupling
3. **Leaky abstractions in L3**: Implementation details in APIs
4. **Inconsistent patterns in L4**: Hard to maintain code

---

*Document Version: 1.0*
*Last Updated: 2026*
