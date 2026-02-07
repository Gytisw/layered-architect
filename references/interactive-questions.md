# Interactive Question Flows

Use these with the platform Question tool (if supported). They are designed to eliminate
open-ended answers early and force measurable inputs before L1.

If the platform does not support interactive questions, translate these to
concise text prompts and require specific, quantified answers.

## Core Concept (Required)

```json
{
  "questions": [
    {
      "header": "Core Concept",
      "question": "What type of system are we building?",
      "options": [
        {"label": "Web App", "description": "User-facing product with UI/UX"},
        {"label": "API Service", "description": "Backend service with external integrations"},
        {"label": "Agent/AI System", "description": "LLM or agent-based workflows"},
        {"label": "Data Pipeline", "description": "ETL, streaming, or analytics pipeline"}
      ]
    }
  ]
}
```

## Deployment Model (Required)

```json
{
  "questions": [
    {
      "header": "Deployment",
      "question": "Preferred deployment model?",
      "options": [
        {"label": "Local-First", "description": "All data stays on device"},
        {"label": "Team Server", "description": "Self-hosted, small team"},
        {"label": "SaaS", "description": "Multi-tenant cloud"},
        {"label": "Hybrid", "description": "Local capture + optional sync"}
      ]
    }
  ]
}
```

## Scale + Latency (Required)

```json
{
  "questions": [
    {
      "header": "Scale",
      "question": "Expected user scale?",
      "options": [
        {"label": "<10 users", "description": "Prototype or single team"},
        {"label": "10-100 users", "description": "Small org"},
        {"label": "100-1,000 users", "description": "Company-wide"},
        {"label": "1,000+ users", "description": "Public scale"}
      ]
    },
    {
      "header": "Latency",
      "question": "Performance requirement?",
      "options": [
        {"label": "<100ms", "description": "Real-time or interactive"},
        {"label": "<1s", "description": "Fast UX"},
        {"label": "<3s", "description": "Standard web latency"},
        {"label": "Batch OK", "description": "Minutes or hours acceptable"}
      ]
    }
  ]
}
```

## Agent/AI System Follow-ups

```json
{
  "questions": [
    {
      "header": "Agent Types",
      "question": "Which agents need support?",
      "options": [
        {"label": "Claude Code", "description": "Anthropic CLI coding agent"},
        {"label": "OpenCode", "description": "Open-source coding agent"},
        {"label": "Custom Agents", "description": "Your internal agents"},
        {"label": "All Major LLMs", "description": "Multi-provider support"}
      ]
    },
    {
      "header": "Data Sensitivity",
      "question": "Data sensitivity level?",
      "options": [
        {"label": "Public", "description": "No confidentiality concerns"},
        {"label": "Internal", "description": "Company data"},
        {"label": "Confidential", "description": "Sensitive logs or IP"},
        {"label": "Regulated", "description": "HIPAA/GDPR/PCI"}
      ]
    }
  ]
}
```

## Finish Gate (Required)

Before proceeding to L1, confirm:
- Core concept selected
- Scale quantified
- Deployment model selected
- At least 3 measurable constraints identified
- User confirms: "Proceed to L1"
