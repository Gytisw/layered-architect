# L5 - Operability and Readiness (Optional)

Use this layer when moving from design to delivery, or when reliability, security, or cost require explicit readiness checks.

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
