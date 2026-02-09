# L4 - Implementation: API Gateway

## Overview

Implementation details, code patterns, and development guidelines for the API Gateway.

---

## File Structure

### Repository Layout

```
api-gateway/
├── cmd/
│   ├── gateway/              # Main gateway binary
│   └── admin/                # Admin CLI tool
├── internal/
│   ├── core/                 # Core gateway engine
│   │   ├── config/
│   │   ├── router/
│   │   ├── upstream/
│   │   ├── server/
│   │   └── pipeline/
│   ├── plugins/              # Built-in plugins
│   │   ├── auth/
│   │   │   ├── jwt/
│   │   │   ├── oauth2/
│   │   │   └── apikey/
│   │   ├── ratelimit/
│   │   ├── cache/
│   │   ├── transform/
│   │   ├── circuitbreaker/
│   │   └── cors/
│   ├── modules/              # Functional modules
│   │   ├── discovery/
│   │   ├── loadbalancer/
│   │   ├── healthcheck/
│   │   └── metrics/
│   └── pkg/                  # Internal packages
│       ├── logger/
│       ├── errors/
│       ├── utils/
│       └── crypto/
├── pkg/                      # Public packages
│   ├── sdk/
│   └── types/
├── configs/
│   ├── gateway.yaml
│   ├── routes/
│   └── plugins/
├── deployments/
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
├── docs/
│   ├── architecture/
│   └── api/
├── scripts/
├── Makefile
├── go.mod
└── README.md
```

---

## Code Patterns

### 1. Plugin Architecture

```go
// internal/plugins/plugin.go
package plugins

import "context"

type Plugin interface {
    Name() string
    Version() string
    Priority() int
    Init(config map[string]interface{}) error
    Execute(ctx context.Context, req *Request) (*Response, error)
}

type Request struct {
    ID       string
    Method   string
    Path     string
    Headers  map[string]string
    Body     []byte
    Context  map[string]interface{}
}

type Response struct {
    StatusCode int
    Headers    map[string]string
    Body       []byte
}
```

### 2. JWT Authentication

```go
// internal/plugins/auth/jwt/plugin.go
package jwt

import (
    "context"
    "fmt"
    "strings"
    "github.com/golang-jwt/jwt/v5"
)

type JWTPlugin struct {
    secret []byte
    issuer string
}

func (p *JWTPlugin) Name() string {
    return "jwt-auth"
}

func (p *JWTPlugin) Version() string {
    return "1.0.0"
}

func (p *JWTPlugin) Priority() int {
    return 100
}

func (p *JWTPlugin) Init(config map[string]interface{}) error {
    secret, ok := config["secret"].(string)
    if !ok {
        return fmt.Errorf("jwt secret required")
    }
    p.secret = []byte(secret)
    p.issuer, _ = config["issuer"].(string)
    return nil
}

func (p *JWTPlugin) Execute(ctx context.Context, req *Request) (*Response, error) {
    authHeader := req.Headers["Authorization"]
    if authHeader == "" {
        return &Response{
            StatusCode: 401,
            Body:       []byte(`{"error":"missing authorization header"}`),
        }, nil
    }

    parts := strings.SplitN(authHeader, " ", 2)
    if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
        return &Response{
            StatusCode: 401,
            Body:       []byte(`{"error":"invalid authorization format"}`),
        }, nil
    }

    token, err := jwt.Parse(parts[1], func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method")
        }
        return p.secret, nil
    })

    if err != nil || !token.Valid {
        return &Response{
            StatusCode: 401,
            Body:       []byte(`{"error":"invalid token"}`),
        }, nil
    }

    if claims, ok := token.Claims.(jwt.MapClaims); ok {
        req.Context["userId"] = claims["sub"]
        req.Context["roles"] = claims["roles"]
    }

    return nil, nil
}
```

### 3. Rate Limiting with Token Bucket

```go
// internal/plugins/ratelimit/token_bucket.go
package ratelimit

import (
    "context"
    "sync"
    "time"
)

type TokenBucket struct {
    capacity   int
    tokens     float64
    refillRate float64
    lastRefill time.Time
    mu         sync.Mutex
}

func NewTokenBucket(capacity int, refillRate float64) *TokenBucket {
    return &TokenBucket{
        capacity:   capacity,
        tokens:     float64(capacity),
        refillRate: refillRate,
        lastRefill: time.Now(),
    }
}

func (tb *TokenBucket) Allow(tokens int) bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(tb.lastRefill).Seconds()
    tb.tokens = min(float64(tb.capacity), tb.tokens+elapsed*tb.refillRate)
    tb.lastRefill = now

    if tb.tokens >= float64(tokens) {
        tb.tokens -= float64(tokens)
        return true
    }
    return false
}

type RateLimitPlugin struct {
    buckets map[string]*TokenBucket
    mu      sync.RWMutex
    limit   int
    window  time.Duration
}

func (p *RateLimitPlugin) Name() string {
    return "rate-limit"
}

func (p *RateLimitPlugin) Version() string {
    return "1.0.0"
}

func (p *RateLimitPlugin) Priority() int {
    return 200
}

func (p *RateLimitPlugin) Init(config map[string]interface{}) error {
    p.buckets = make(map[string]*TokenBucket)
    p.limit = 100
    p.window = time.Minute
    return nil
}

func (p *RateLimitPlugin) Execute(ctx context.Context, req *Request) (*Response, error) {
    clientID := req.Headers["X-API-Key"]
    if clientID == "" {
        clientID = req.Context["clientIP"].(string)
    }

    p.mu.Lock()
    bucket, exists := p.buckets[clientID]
    if !exists {
        bucket = NewTokenBucket(p.limit, float64(p.limit)/p.window.Seconds())
        p.buckets[clientID] = bucket
    }
    p.mu.Unlock()

    if !bucket.Allow(1) {
        return &Response{
            StatusCode: 429,
            Headers: map[string]string{
                "Retry-After": "60",
            },
            Body: []byte(`{"error":"rate limit exceeded"}`),
        }, nil
    }

    return nil, nil
}
```

### 4. Circuit Breaker Pattern

```go
// internal/plugins/circuitbreaker/plugin.go
package circuitbreaker

import (
    "context"
    "errors"
    "sync"
    "time"
)

type State int

const (
    StateClosed State = iota
    StateOpen
    StateHalfOpen
)

type CircuitBreaker struct {
    failureThreshold int
    recoveryTimeout  time.Duration
    halfOpenMaxCalls int
    
    state            State
    failures         int
    successes        int
    lastFailureTime  time.Time
    mu               sync.Mutex
}

func NewCircuitBreaker(failureThreshold int, recoveryTimeout time.Duration, halfOpenMaxCalls int) *CircuitBreaker {
    return &CircuitBreaker{
        failureThreshold: failureThreshold,
        recoveryTimeout:  recoveryTimeout,
        halfOpenMaxCalls: halfOpenMaxCalls,
        state:            StateClosed,
    }
}

func (cb *CircuitBreaker) Allow() bool {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    switch cb.state {
    case StateClosed:
        return true
    case StateOpen:
        if time.Since(cb.lastFailureTime) > cb.recoveryTimeout {
            cb.state = StateHalfOpen
            cb.successes = 0
            cb.failures = 0
            return true
        }
        return false
    case StateHalfOpen:
        return cb.successes+cb.failures < cb.halfOpenMaxCalls
    }
    return false
}

func (cb *CircuitBreaker) RecordSuccess() {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    switch cb.state {
    case StateHalfOpen:
        cb.successes++
        if cb.successes >= cb.halfOpenMaxCalls {
            cb.state = StateClosed
            cb.failures = 0
        }
    case StateClosed:
        cb.failures = 0
    }
}

func (cb *CircuitBreaker) RecordFailure() {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    cb.failures++
    cb.lastFailureTime = time.Now()

    switch cb.state {
    case StateHalfOpen:
        cb.state = StateOpen
    case StateClosed:
        if cb.failures >= cb.failureThreshold {
            cb.state = StateOpen
        }
    }
}
```

### 5. Configuration Management

```go
// internal/core/config/loader.go
package config

import (
    "fmt"
    "os"
    "gopkg.in/yaml.v3"
)

type Config struct {
    Server    ServerConfig    `yaml:"server"`
    Routes    []RouteConfig   `yaml:"routes"`
    Plugins   []PluginConfig  `yaml:"plugins"`
    Upstream  UpstreamConfig  `yaml:"upstream"`
    Logging   LoggingConfig   `yaml:"logging"`
}

type ServerConfig struct {
    HTTP  HTTPConfig  `yaml:"http"`
    HTTPS HTTPSConfig `yaml:"https"`
}

type HTTPConfig struct {
    Enabled bool   `yaml:"enabled"`
    Port    int    `yaml:"port"`
}

type HTTPSConfig struct {
    Enabled  bool   `yaml:"enabled"`
    Port     int    `yaml:"port"`
    CertFile string `yaml:"cert_file"`
    KeyFile  string `yaml:"key_file"`
}

type RouteConfig struct {
    Name        string                 `yaml:"name"`
    Path        string                 `yaml:"path"`
    Methods     []string               `yaml:"methods"`
    Upstream    string                 `yaml:"upstream"`
    Plugins     []string               `yaml:"plugins"`
    StripPath   bool                   `yaml:"strip_path"`
    Middleware  map[string]interface{} `yaml:"middleware"`
}

type PluginConfig struct {
    Name   string                 `yaml:"name"`
    Config map[string]interface{} `yaml:"config"`
}

type UpstreamConfig struct {
    Timeout     int    `yaml:"timeout"`
    KeepAlive   bool   `yaml:"keep_alive"`
    MaxConnections int `yaml:"max_connections"`
}

type LoggingConfig struct {
    Level  string `yaml:"level"`
    Format string `yaml:"format"`
}

func Load(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("failed to read config file: %w", err)
    }

    var cfg Config
    if err := yaml.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("failed to parse config: %w", err)
    }

    return &cfg, nil
}
```

### 6. HTTP Server with Graceful Shutdown

```go
// internal/core/server/server.go
package server

import (
    "context"
    "fmt"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

type Server struct {
    httpServer  *http.Server
    httpsServer *http.Server
    router      http.Handler
}

func New(cfg Config, router http.Handler) *Server {
    s := &Server{
        router: router,
    }

    if cfg.HTTP.Enabled {
        s.httpServer = &http.Server{
            Addr:         fmt.Sprintf(":%d", cfg.HTTP.Port),
            Handler:      router,
            ReadTimeout:  30 * time.Second,
            WriteTimeout: 30 * time.Second,
            IdleTimeout:  120 * time.Second,
        }
    }

    if cfg.HTTPS.Enabled {
        s.httpsServer = &http.Server{
            Addr:         fmt.Sprintf(":%d", cfg.HTTPS.Port),
            Handler:      router,
            ReadTimeout:  30 * time.Second,
            WriteTimeout: 30 * time.Second,
            IdleTimeout:  120 * time.Second,
        }
    }

    return s
}

func (s *Server) Start() error {
    errChan := make(chan error, 2)

    if s.httpServer != nil {
        go func() {
            errChan <- s.httpServer.ListenAndServe()
        }()
    }

    if s.httpsServer != nil {
        go func() {
            errChan <- s.httpsServer.ListenAndServeTLS("", "")
        }()
    }

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

    select {
    case err := <-errChan:
        return err
    case <-quit:
        return s.Shutdown(context.Background())
    }
}

func (s *Server) Shutdown(ctx context.Context) error {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    if s.httpServer != nil {
        if err := s.httpServer.Shutdown(ctx); err != nil {
            return err
        }
    }

    if s.httpsServer != nil {
        if err := s.httpsServer.Shutdown(ctx); err != nil {
            return err
        }
    }

    return nil
}
```

---

## Database Schema (Redis)

### Rate Limiting Keys

```
# Token bucket state
ratelimit:{client_id}:tokens       # Current token count (float)
ratelimit:{client_id}:last_refill  # Last refill timestamp

# Fixed window counters
ratelimit:{client_id}:{window}     # Request count for time window
```

### Cache Keys

```
# Response cache
cache:{method}:{path}:{query_hash}  # Cached response
cache:{key}:tags                     # Cache tags for invalidation

# Session cache
session:{session_id}                 # Session data
```

### Service Discovery

```
# Service registry
services:{service_name}:instances   # Set of instance IDs
service:{instance_id}:metadata      # Hash of instance metadata
service:{instance_id}:health        # Health status
```

---

## Docker Configuration

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway ./cmd/gateway

FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /app/gateway .
COPY configs/ ./configs/

EXPOSE 8080 8443 9090

CMD ["./gateway", "-config", "./configs/gateway.yaml"]
```

---

## Kubernetes Deployment

```yaml
# deployments/kubernetes/gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: gateway
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
        - name: gateway
          image: company/api-gateway:latest
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 8443
              name: https
            - containerPort: 9090
              name: metrics
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: config
              mountPath: /app/configs
            - name: certs
              mountPath: /app/certs
      volumes:
        - name: config
          configMap:
            name: gateway-config
        - name: certs
          secret:
            secretName: gateway-certs
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: gateway
spec:
  selector:
    app: api-gateway
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: https
      port: 443
      targetPort: 8443
    - name: metrics
      port: 9090
  type: LoadBalancer
```

---

## Testing Strategy

### Unit Test Example

```go
// internal/plugins/auth/jwt/plugin_test.go
package jwt

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestJWTPlugin_Execute(t *testing.T) {
    plugin := &JWTPlugin{}
    err := plugin.Init(map[string]interface{}{
        "secret": "test-secret-key",
    })
    assert.NoError(t, err)

    tests := []struct {
        name       string
        headers    map[string]string
        wantStatus int
    }{
        {
            name:       "missing authorization header",
            headers:    map[string]string{},
            wantStatus: 401,
        },
        {
            name:       "invalid format",
            headers:    map[string]string{"Authorization": "Basic dXNlcjpwYXNz"},
            wantStatus: 401,
        },
        {
            name:       "invalid token",
            headers:    map[string]string{"Authorization": "Bearer invalid-token"},
            wantStatus: 401,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := &Request{
                Headers: tt.headers,
                Context: make(map[string]interface{}),
            }
            resp, err := plugin.Execute(context.Background(), req)
            assert.NoError(t, err)
            assert.Equal(t, tt.wantStatus, resp.StatusCode)
        })
    }
}
```

### Integration Test Example

```go
// tests/integration/gateway_test.go
package integration

import (
    "net/http"
    "net/http/httptest"
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestGateway_EndToEnd(t *testing.T) {
    // Start test upstream server
    upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{"status":"ok"}`))
    }))
    defer upstream.Close()

    // Configure and start gateway
    gateway := NewTestGateway(upstream.URL)
    defer gateway.Shutdown()

    // Make request through gateway
    resp, err := http.Get(gateway.URL + "/api/test")
    assert.NoError(t, err)
    assert.Equal(t, http.StatusOK, resp.StatusCode)
}
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/gateway.yml
name: API Gateway CI/CD

on:
  push:
    paths:
      - 'api-gateway/**'
      - '.github/workflows/gateway.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test ./...
      - run: go build -v ./...

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: company/api-gateway:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - run: |
          kubectl set image deployment/api-gateway \
            gateway=company/api-gateway:${{ github.sha }} \
            -n gateway
```

---

## Implementation Details

- [Key implementation notes, scaling constraints, or performance considerations]

## Validation Commands

```bash
# Example validation commands
python scripts/arch.py validate --layer L4 --path .plan
```

---

## Decision Log

1. **Decision**: [Key implementation decision]
   - **Rationale**: [Why this decision was made]
   - **Impact**: [What it affects downstream]

---

*Document Version: 1.0*  
*Based on L3: API Gateway Component Design*
