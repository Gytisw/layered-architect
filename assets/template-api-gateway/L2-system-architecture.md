# L2 - System Architecture: API Gateway

## Overview

The API Gateway serves as a reverse proxy, request router, and policy enforcement point for all microservices. It provides a unified API surface while delegating business logic to backend services.

---

## Subsystems

### 1. Authentication & Authorization (Auth Service)

**Responsibility**: Identity verification and access control

**Components**:
- JWT Validator
- OAuth 2.0 / OIDC Provider Integration
- API Key Manager
- RBAC Engine
- Session Store

**Key Features**:
- Token validation (JWT, opaque tokens)
- OAuth 2.0 flows (Authorization Code, Client Credentials, PKCE)
- API key generation and validation
- Role-based access control (RBAC)
- Token refresh and revocation

**Integrations**:
- Identity Providers (Auth0, Keycloak, Okta)
- LDAP/Active Directory
- Custom auth services

### 2. Rate Limiting & Throttling

**Responsibility**: Traffic control and abuse prevention

**Components**:
- Rate Limit Engine
- Quota Manager
- Throttling Algorithm (Token Bucket, Leaky Bucket)
- Distributed Counter (Redis)

**Key Features**:
- Per-client rate limits (IP, API key, user)
- Tiered quotas (free, pro, enterprise)
- Burst handling with smoothing
- Geographic rate limiting
- Dynamic throttling based on backend health

**Configuration**:
```yaml
rate_limits:
  default:
    requests_per_minute: 60
    burst: 10
  authenticated:
    requests_per_minute: 1000
    burst: 100
  enterprise:
    requests_per_minute: 10000
    burst: 1000
```

### 3. Routing Engine

**Responsibility**: Request routing to backend services

**Components**:
- Route Matcher
- Load Balancer
- Service Registry Client
- Path Rewriter
- Header Injector

**Key Features**:
- Path-based routing (`/users/*` → User Service)
- Host-based routing (`api.service.com` → Service)
- Header-based routing (canary by header)
- Method-based routing
- Weighted routing for canary deployments
- Dynamic route updates without restart

**Route Types**:
- Direct routes: Static backend URLs
- Service discovery: Consul, Eureka, Kubernetes
- Lambda/Function: Serverless backends
- External: Third-party APIs

### 4. Request/Response Transformation

**Responsibility**: Protocol and format adaptation

**Components**:
- Request Transformer
- Response Transformer
- Protocol Converter
- Template Engine

**Key Features**:
- JSON ↔ XML conversion
- gRPC ↔ HTTP/REST translation
- Header manipulation (add/remove/modify)
- Body transformation (JSONPath, templates)
- Request/response logging

**Transformation Pipeline**:
```
Incoming Request
    ↓
Request Validation
    ↓
Header Injection (correlation IDs, auth context)
    ↓
Body Transformation
    ↓
Backend Request
    ↓
Backend Response
    ↓
Response Transformation
    ↓
Caching Layer
    ↓
Outgoing Response
```

### 5. Load Balancing & Health Checks

**Responsibility**: Traffic distribution and service health

**Components**:
- Load Balancer (Round Robin, Least Connections, Consistent Hash)
- Health Check Prober
- Circuit Breaker
- Retry Handler

**Key Features**:
- Multiple load balancing algorithms
- Active and passive health checks
- Circuit breaker pattern (prevent cascade failures)
- Automatic retry with exponential backoff
- Sticky sessions for stateful services

**Health Check Configuration**:
```yaml
health_checks:
  interval: 10s
  timeout: 5s
  healthy_threshold: 2
  unhealthy_threshold: 3
  path: /health
  expected_status: 200
```

### 6. Caching Layer

**Responsibility**: Response caching for performance

**Components**:
- Cache Store (Redis)
- Cache Key Generator
- TTL Manager
- Cache Invalidator

**Key Features**:
- Response caching based on cache headers
- Cache key customization
- Cache warming
- Selective cache bypass
- Cache invalidation API

**Caching Strategy**:
| Endpoint | Cache Duration | Cache Key |
|----------|----------------|-----------|
| GET /users/:id | 5 minutes | user:{id} |
| GET /products | 1 minute | products:{query_params} |
| GET /config | 1 hour | config:{version} |

### 7. Observability & Analytics

**Responsibility**: Monitoring, logging, and analytics

**Components**:
- Metrics Collector (Prometheus)
- Distributed Tracer (Jaeger/Zipkin)
- Access Logger
- Analytics Engine
- Alert Manager

**Key Features**:
- Request/response logging
- Distributed tracing (OpenTelemetry)
- Real-time metrics dashboard
- Per-endpoint analytics
- SLA monitoring and alerting
- Cost attribution by consumer

**Metrics Collected**:
- Request count, rate, latency (p50, p95, p99)
- Error rates by status code
- Backend response times
- Cache hit/miss ratios
- Rate limit violations
- Active connections

---

## System Boundaries

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL NETWORK                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Web Apps │  │Mobile App│  │ Partner  │  │  IoT     │  │  CLI     │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼ TLS 1.3
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CDN / WAF                                        │
│                    (DDoS Protection, Edge Caching)                           │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY CLUSTER                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CONTROL PLANE                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │    │
│  │  │   Admin     │  │  Config     │  │   Service   │  │  Metrics  │  │    │
│  │  │   API       │  │  Store      │  │   Registry  │  │  & Logs   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       DATA PLANE                                     │    │
│  │                                                                      │    │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │    │
│  │   │   Auth   │──▶│  Rate    │──▶│  Route   │──▶│  Cache   │        │    │
│  │   │  Layer   │   │  Limit   │   │  Engine  │   │  Layer   │        │    │
│  │   └──────────┘   └──────────┘   └────┬─────┘   └────┬─────┘        │    │
│  │                                      │              │              │    │
│  │   ┌──────────────────────────────────┘              │              │    │
│  │   ▼                                                 ▼              │    │
│  │   ┌──────────┐                           ┌────────────────────┐   │    │
│  │   │ Transform│◀──────────────────────────│   Cache Store      │   │    │
│  │   │  Layer   │                           │   (Redis Cluster)  │   │    │
│  │   └────┬─────┘                           └────────────────────┘   │    │
│  │        │                                                           │    │
│  │   ┌────┴────────────────────────────────────────────────────────┐  │    │
│  │   ▼                                                              │  │    │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐                    │  │    │
│  │   │  Load    │──▶│ Circuit  │──▶│  Retry   │                    │  │    │
│  │   │ Balancer │   │ Breaker  │   │ Handler  │                    │  │    │
│  │   └──────────┘   └──────────┘   └──────────┘                    │  │    │
│  │                                                                  │  │    │
│  └──────────────────────────────────────────────────────────────────┘  │    │
│                                                                         │    │
└─────────────────────────────────────────────────────────────────────────┘    │
                                       │
                                       ▼ Internal Network (mTLS)
┌──────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND SERVICES                                      │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  User    │  │ Product  │  │  Order   │  │ Payment  │  │Analytics │       │
│  │ Service  │  │ Catalog  │  │ Service  │  │ Gateway  │  │ Service  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │Inventory │  │ Shipping │  │ Notification        │  │  ...       │         │
│  │ Service  │  │ Service  │  │ Service  │  │          │                      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Boundary Rules

1. **Gateway Isolation**: Gateway instances run in isolated network segments
2. **mTLS Everywhere**: All inter-service communication uses mutual TLS
3. **No Direct Access**: Clients cannot access backend services directly
4. **Control Plane Separation**: Administrative APIs isolated from data plane
5. **Multi-AZ Deployment**: Gateway instances distributed across availability zones

---

## Data Flow

### Flow 1: Authenticated API Request

```
┌──────────┐     ┌─────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│ CDN │────▶│  Gateway │────▶│   Auth   │────▶│  Backend │
└──────────┘     └─────┘     │  Instance│     │ Service  │     │ Service  │
                             └──────────┘     └──────────┘     └──────────┘
                                    │                               │
                                    │    Route                      │
                                    │◀──────────────────────────────┘
                                    │    Response
                                    ▼
                              ┌──────────┐
                              │  Client  │
                              └──────────┘
```

**Steps**:
1. Client sends request with Authorization header
2. CDN/WAF processes request (caching, security)
3. Gateway validates JWT signature and claims
4. Gateway checks rate limits for client
5. Gateway matches route and selects backend
6. Gateway applies request transformations
7. Gateway forwards request to backend service
8. Backend processes and returns response
9. Gateway applies response transformations
10. Gateway returns response to client

### Flow 2: Service Discovery & Routing

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Gateway    │◀───────▶│   Consul     │◀───────▶│   Services   │
│   Instance   │  Watch  │   (Registry) │ Register│  (Backend)   │
└──────────────┘         └──────────────┘         └──────────────┘
       │
       │ Periodic Health Check
       ▼
┌──────────────┐
│   Backend    │
│   Service    │
└──────────────┘
```

**Steps**:
1. Backend services register with Consul on startup
2. Gateway watches Consul for service changes
3. Client makes request to `/api/v1/users`
4. Gateway resolves route: `/api/v1/users/*` → user-service
5. Gateway queries Consul for healthy user-service instances
6. Gateway applies load balancing algorithm
7. Gateway forwards request to selected instance
8. Gateway monitors response and updates health status

### Flow 3: Rate Limiting

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────▶│   Gateway    │────▶│    Redis     │────▶│  Allow   │
│  Request │     │ Rate Limiter │     │   Counter    │     │  Deny    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
```

**Token Bucket Algorithm**:
1. Client request arrives
2. Gateway extracts client identifier (API key, IP, user ID)
3. Gateway queries Redis for current token count
4. If tokens available: decrement counter, allow request
5. If no tokens: return 429 Too Many Requests
6. Tokens refill at configured rate

### Flow 4: Distributed Tracing

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  Gateway │────▶│  User    │────▶│  Order   │
│  Request │     │ (Root    │     │  Service │     │  Service │
│          │     │  Span)   │     │ (Child)  │     │ (Child)  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                                              │
       └──────────────────────────────────────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │   Jaeger     │
                    │   (Traces)   │
                    └──────────────┘
```

**Trace Context Propagation**:
1. Gateway generates trace ID and span ID
2. Gateway adds headers: `x-trace-id`, `x-span-id`
3. Backend services create child spans with parent reference
4. All spans sent to Jaeger collector
5. Full request path visualized in Jaeger UI

---

## Interfaces

### API Contracts

#### Admin API

```yaml
openapi: 3.0.0
info:
  title: Gateway Admin API
  version: 1.0.0

paths:
  /admin/v1/routes:
    get:
      summary: List all routes
      security:
        - bearerAuth: []
      responses:
        200:
          description: List of routes
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Route'
    
    post:
      summary: Create new route
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RouteCreate'
      responses:
        201:
          description: Route created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Route'

  /admin/v1/routes/{id}:
    put:
      summary: Update route
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RouteUpdate'
      responses:
        200:
          description: Route updated

    delete:
      summary: Delete route
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        204:
          description: Route deleted

  /admin/v1/cache/purge:
    post:
      summary: Purge cache
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                pattern:
                  type: string
                  description: Cache key pattern to purge
      responses:
        200:
          description: Cache purged

components:
  schemas:
    Route:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        host:
          type: string
        path:
          type: string
        methods:
          type: array
          items:
            type: string
        upstream:
          type: object
          properties:
            url:
              type: string
            load_balancer:
              type: string
              enum: [round_robin, least_conn, ip_hash]
        plugins:
          type: array
          items:
            type: object
        created_at:
          type: string
          format: date-time

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

#### Client Gateway API

All client requests follow this pattern:

```yaml
# Request
GET /api/v1/users/123 HTTP/1.1
Host: api.company.com
Authorization: Bearer {jwt_token}
X-Request-ID: {uuid}
Accept: application/json

# Response
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: {uuid}
X-Cache-Status: MISS
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642681200

{
  "id": "123",
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Event Contracts

#### Gateway Events

```protobuf
syntax = "proto3";

message RouteCreated {
  string route_id = 1;
  string name = 2;
  string path = 3;
  string upstream_url = 4;
  int64 timestamp = 5;
}

message RouteUpdated {
  string route_id = 1;
  map<string, string> changes = 2;
  int64 timestamp = 3;
}

message RequestLogged {
  string request_id = 1;
  string client_ip = 2;
  string method = 3;
  string path = 4;
  int32 status_code = 5;
  int64 latency_ms = 6;
  string user_agent = 7;
  string api_key = 8;
  int64 timestamp = 9;
}

message RateLimitExceeded {
  string client_id = 1;
  string path = 2;
  int32 limit = 3;
  int64 reset_time = 4;
  int64 timestamp = 5;
}
```

---

## Capacity Planning

| Component | Initial | Scale 1 | Scale 2 | Scale 3 |
|-----------|---------|---------|---------|---------|
| Gateway Instances | 3 | 10 | 25 | 100 |
| Throughput (req/s) | 150,000 | 500,000 | 1,250,000 | 5,000,000 |
| Redis Nodes | 3 | 6 | 12 | 24 |
| Cache Memory | 30 GB | 100 GB | 250 GB | 1 TB |
| Kafka Partitions | 12 | 48 | 120 | 480 |

### Scaling Triggers

| Metric | Scale Up Threshold | Scale Down Threshold |
|--------|-------------------|---------------------|
| CPU Usage | > 70% for 5 min | < 30% for 10 min |
| Memory Usage | > 80% for 5 min | < 40% for 10 min |
| Request Latency (p99) | > 50ms for 3 min | < 20ms for 10 min |
| Error Rate | > 0.1% for 2 min | < 0.01% for 5 min |
| Active Connections | > 80% capacity | < 40% capacity |

---

*Document Version: 1.0*  
*Based on L1: API Gateway Meta-Architecture*
