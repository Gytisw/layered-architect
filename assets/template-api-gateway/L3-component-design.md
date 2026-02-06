# L3 - Component Design: API Gateway

## Overview

Detailed component design for the API Gateway, including module breakdowns, plugin architecture, and configuration management.

---

## Module Breakdown

### 1. Core Gateway Engine

```
gateway-core/
├── src/
│   ├── config/
│   │   ├── ConfigLoader.ts
│   │   ├── ConfigValidator.ts
│   │   └── ConfigStore.ts
│   ├── router/
│   │   ├── RouteMatcher.ts
│   │   ├── RouteRegistry.ts
│   │   └── PathRewriter.ts
│   ├── upstream/
│   │   ├── LoadBalancer.ts
│   │   ├── HealthChecker.ts
│   │   ├── ConnectionPool.ts
│   │   └── UpstreamSelector.ts
│   ├── server/
│   │   ├── HttpServer.ts
│   │   ├── HttpsServer.ts
│   │   ├── Http2Server.ts
│   │   └── RequestHandler.ts
│   ├── pipeline/
│   │   ├── PluginChain.ts
│   │   ├── RequestPipeline.ts
│   │   └── ResponsePipeline.ts
│   └── utils/
│       ├── Logger.ts
│       ├── Metrics.ts
│       └── ErrorHandler.ts
```

#### Key Components

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| ConfigLoader | Load and merge configurations | YAML/JSON parsers |
| RouteMatcher | Match requests to routes | Radix tree, Regex |
| LoadBalancer | Distribute traffic upstream | Multiple algorithms |
| HealthChecker | Monitor upstream health | HTTP probes |
| PluginChain | Execute plugins in order | Middleware pattern |

### 2. Authentication Module

```
auth-module/
├── src/
│   ├── strategies/
│   │   ├── JwtStrategy.ts
│   │   ├── OAuth2Strategy.ts
│   │   ├── ApiKeyStrategy.ts
│   │   └── MtlsStrategy.ts
│   ├── validators/
│   │   ├── JwtValidator.ts
│   │   ├── ScopeValidator.ts
│   │   └── ClaimsValidator.ts
│   ├── cache/
│   │   └── TokenCache.ts
│   └── middleware/
│       └── AuthMiddleware.ts
```

**JWT Validation Flow**:
```
Request with JWT
    ↓
Extract Token from Header
    ↓
Verify Signature (RS256)
    ↓
Validate Claims (exp, iss, aud)
    ↓
Check Cache (avoid repeat validation)
    ↓
Inject User Context to Request
    ↓
Continue to Next Plugin
```

### 3. Rate Limiting Module

```
rate-limiter/
├── src/
│   ├── algorithms/
│   │   ├── TokenBucket.ts
│   │   ├── LeakyBucket.ts
│   │   ├── FixedWindow.ts
│   │   └── SlidingWindow.ts
│   ├── stores/
│   │   ├── RedisStore.ts
│   │   ├── InMemoryStore.ts
│   │   └── ClusterStore.ts
│   ├── resolvers/
│   │   ├── IpResolver.ts
│   │   ├── ApiKeyResolver.ts
│   │   ├── UserResolver.ts
│   │   └── HeaderResolver.ts
│   └── middleware/
│       └── RateLimitMiddleware.ts
```

**Token Bucket Algorithm**:
```typescript
// src/algorithms/TokenBucket.ts
export class TokenBucket {
  constructor(
    private capacity: number,
    private refillRate: number, // tokens per second
    private store: TokenStore
  ) {}

  async consume(key: string, tokens: number = 1): Promise<ConsumeResult> {
    const now = Date.now();
    const bucketKey = `bucket:${key}`;
    
    const bucket = await this.store.get(bucketKey) || {
      tokens: this.capacity,
      lastRefill: now
    };

    // Calculate tokens to add based on time elapsed
    const elapsed = (now - bucket.lastRefill) / 1000;
    const tokensToAdd = elapsed * this.refillRate;
    bucket.tokens = Math.min(this.capacity, bucket.tokens + tokensToAdd);
    bucket.lastRefill = now;

    if (bucket.tokens >= tokens) {
      bucket.tokens -= tokens;
      await this.store.set(bucketKey, bucket);
      
      return {
        allowed: true,
        remaining: Math.floor(bucket.tokens),
        resetTime: now + ((this.capacity - bucket.tokens) / this.refillRate) * 1000
      };
    }

    await this.store.set(bucketKey, bucket);
    
    return {
      allowed: false,
      remaining: 0,
      resetTime: now + ((tokens - bucket.tokens) / this.refillRate) * 1000,
      retryAfter: Math.ceil((tokens - bucket.tokens) / this.refillRate)
    };
  }
}
```

### 4. Service Discovery Module

```
service-discovery/
├── src/
│   ├── providers/
│   │   ├── ConsulProvider.ts
│   │   ├── EurekaProvider.ts
│   │   ├── KubernetesProvider.ts
│   │   └── StaticProvider.ts
│   ├── health/
│   │   ├── HealthChecker.ts
│   │   ├── HealthAggregator.ts
│   │   └── HealthReporter.ts
│   ├── cache/
│   │   └── ServiceCache.ts
│   └── watcher/
│       └── ServiceWatcher.ts
```

### 5. Transformation Module

```
transformation/
├── src/
│   ├── request/
│   │   ├── HeaderTransformer.ts
│   │   ├── BodyTransformer.ts
│   │   ├── QueryTransformer.ts
│   │   └── PathTransformer.ts
│   ├── response/
│   │   ├── HeaderTransformer.ts
│   │   ├── BodyTransformer.ts
│   │   └── StatusTransformer.ts
│   ├── template/
│   │   ├── TemplateEngine.ts
│   │   ├── JsonPathEngine.ts
│   │   └── JqEngine.ts
│   └── protocol/
│       ├── GrpcTranslator.ts
│       └── WebSocketTranslator.ts
```

### 6. Caching Module

```
caching/
├── src/
│   ├── store/
│   │   ├── RedisCache.ts
│   │   ├── InMemoryCache.ts
│   │   └── TieredCache.ts
│   ├── policies/
│   │   ├── CachePolicy.ts
│   │   ├── TtlPolicy.ts
│   │   └── VaryPolicy.ts
│   ├── key/
│   │   ├── CacheKeyBuilder.ts
│   │   └── CacheKeyParser.ts
│   └── invalidation/
│       ├── CacheInvalidator.ts
│       └── TagBasedInvalidator.ts
```

### 7. Observability Module

```
observability/
├── src/
│   ├── tracing/
│   │   ├── Tracer.ts
│   │   ├── SpanBuilder.ts
│   │   └── Propagator.ts
│   ├── metrics/
│   │   ├── MetricsCollector.ts
│   │   ├── PrometheusExporter.ts
│   │   └── StatsdExporter.ts
│   ├── logging/
│   │   ├── AccessLogger.ts
│   │   ├── StructuredLogger.ts
│   │   └── LogFormatter.ts
│   └── analytics/
│       ├── AnalyticsCollector.ts
│       └── UsageReporter.ts
```

---

## Plugin Architecture

### Plugin Interface

```typescript
// src/plugins/Plugin.ts
export interface Plugin {
  name: string;
  version: string;
  priority: number; // Execution order
  
  // Lifecycle hooks
  init(config: any): Promise<void>;
  
  // Request phase
  access?(request: GatewayRequest): Promise<GatewayRequest | Response>;
  
  // Before upstream call
  preread?(request: GatewayRequest): Promise<void>;
  
  // After upstream call
  postread?(response: GatewayResponse): Promise<GatewayResponse>;
  
  // Response phase
  response?(response: GatewayResponse): Promise<GatewayResponse>;
  
  // Error handling
  error?(error: Error, context: PluginContext): Promise<Response | void>;
  
  // Cleanup
  destroy(): Promise<void>;
}

export interface GatewayRequest {
  id: string;
  method: string;
  url: URL;
  headers: Headers;
  body: ReadableStream;
  context: RequestContext;
}

export interface GatewayResponse {
  status: number;
  headers: Headers;
  body: ReadableStream;
  upstreamLatency: number;
}
```

### Core Plugins

#### 1. JWT Auth Plugin

```typescript
// src/plugins/JwtAuthPlugin.ts
export class JwtAuthPlugin implements Plugin {
  name = 'jwt-auth';
  version = '1.0.0';
  priority = 100; // Run early
  
  private validator: JwtValidator;
  private cache: TokenCache;
  
  async init(config: JwtAuthConfig): Promise<void> {
    this.validator = new JwtValidator({
      jwksUrl: config.jwksUrl,
      issuer: config.issuer,
      audience: config.audience,
    });
    this.cache = new TokenCache(config.cacheTtl);
  }
  
  async access(request: GatewayRequest): Promise<GatewayRequest> {
    const authHeader = request.headers.get('authorization');
    
    if (!authHeader?.startsWith('Bearer ')) {
      throw new UnauthorizedError('Missing or invalid authorization header');
    }
    
    const token = authHeader.substring(7);
    
    // Check cache first
    let payload = await this.cache.get(token);
    
    if (!payload) {
      payload = await this.validator.verify(token);
      await this.cache.set(token, payload);
    }
    
    // Inject user context
    request.context.userId = payload.sub;
    request.context.roles = payload.roles;
    request.context.scopes = payload.scope?.split(' ') || [];
    
    return request;
  }
}
```

#### 2. Rate Limit Plugin

```typescript
// src/plugins/RateLimitPlugin.ts
export class RateLimitPlugin implements Plugin {
  name = 'rate-limit';
  version = '1.0.0';
  priority = 200;
  
  private limiter: RateLimiter;
  
  async init(config: RateLimitConfig): Promise<void> {
    this.limiter = new RateLimiter({
      algorithm: config.algorithm || 'token_bucket',
      store: new RedisStore(config.redisUrl),
      defaultLimit: config.requestsPerMinute || 60,
      defaultWindow: 60,
    });
  }
  
  async access(request: GatewayRequest): Promise<GatewayRequest> {
    const clientId = this.extractClientId(request);
    const key = `ratelimit:${clientId}`;
    
    const result = await this.limiter.consume(key);
    
    // Add rate limit headers
    request.context.rateLimit = {
      limit: result.limit,
      remaining: result.remaining,
      reset: result.resetTime,
    };
    
    if (!result.allowed) {
      throw new RateLimitError('Rate limit exceeded', {
        retryAfter: result.retryAfter,
      });
    }
    
    return request;
  }
  
  async response(response: GatewayResponse): Promise<GatewayResponse> {
    // Add rate limit headers to response
    const limit = response.request?.context.rateLimit;
    if (limit) {
      response.headers.set('X-RateLimit-Limit', limit.limit.toString());
      response.headers.set('X-RateLimit-Remaining', limit.remaining.toString());
      response.headers.set('X-RateLimit-Reset', limit.reset.toString());
    }
    return response;
  }
  
  private extractClientId(request: GatewayRequest): string {
    // Priority: API Key > User ID > IP Address
    return request.context.apiKey 
      || request.context.userId 
      || request.context.clientIp;
  }
}
```

#### 3. Cache Plugin

```typescript
// src/plugins/CachePlugin.ts
export class CachePlugin implements Plugin {
  name = 'cache';
  version = '1.0.0';
  priority = 50;
  
  private cache: CacheStore;
  
  async init(config: CacheConfig): Promise<void> {
    this.cache = new RedisCache(config.redisUrl);
  }
  
  async access(request: GatewayRequest): Promise<GatewayRequest | Response> {
    // Only cache GET requests
    if (request.method !== 'GET') {
      return request;
    }
    
    const cacheKey = this.buildCacheKey(request);
    const cached = await this.cache.get(cacheKey);
    
    if (cached) {
      return new Response(cached.body, {
        status: cached.status,
        headers: new Headers({
          ...cached.headers,
          'X-Cache-Status': 'HIT',
        }),
      });
    }
    
    request.context.cacheKey = cacheKey;
    return request;
  }
  
  async response(response: GatewayResponse): Promise<GatewayResponse> {
    const cacheKey = response.request?.context.cacheKey;
    
    if (cacheKey && this.isCacheable(response)) {
      const ttl = this.extractTtl(response);
      await this.cache.set(cacheKey, {
        status: response.status,
        headers: Object.fromEntries(response.headers),
        body: await response.body.text(),
      }, ttl);
      
      response.headers.set('X-Cache-Status', 'MISS');
    }
    
    return response;
  }
  
  private buildCacheKey(request: GatewayRequest): string {
    const parts = [
      'cache',
      request.url.pathname,
      request.url.search,
      request.headers.get('accept') || '',
    ];
    return parts.join(':');
  }
  
  private isCacheable(response: GatewayResponse): boolean {
    return response.status === 200 && 
           !response.headers.get('cache-control')?.includes('no-store');
  }
}
```

---

## Configuration Schema

### Route Configuration

```yaml
# config/routes.yaml
routes:
  - name: user-service
    host: api.example.com
    path: /api/v1/users/*
    methods: [GET, POST, PUT, DELETE]
    strip_path: true
    preserve_host: false
    
    upstream:
      type: service_discovery
      service_name: user-service
      load_balancer: least_conn
      health_check:
        path: /health
        interval: 10s
        timeout: 5s
        healthy_threshold: 2
        unhealthy_threshold: 3
      
      # Fallback configuration
      fallback:
        status_code: 503
        body: '{"error": "Service temporarily unavailable"}'
    
    plugins:
      - name: jwt-auth
        config:
          jwks_url: https://auth.example.com/.well-known/jwks.json
          issuer: https://auth.example.com
          audience: api.example.com
      
      - name: rate-limit
        config:
          algorithm: token_bucket
          requests_per_minute: 1000
          burst: 100
      
      - name: cache
        config:
          ttl: 300  # 5 minutes
          vary_headers: [Accept, Accept-Encoding]
      
      - name: request-transform
        config:
          add_headers:
            X-Request-ID: ${request.id}
            X-User-ID: ${context.userId}
          remove_headers:
            - Authorization
      
      - name: circuit-breaker
        config:
          failure_threshold: 5
          recovery_timeout: 30s
          half_open_max_calls: 3
    
    # CORS configuration
    cors:
      origins: ["https://app.example.com"]
      methods: [GET, POST, PUT, DELETE, OPTIONS]
      headers: [Authorization, Content-Type, X-Request-ID]
      credentials: true
      max_age: 86400

  - name: public-products
    path: /api/v1/products
    methods: [GET]
    upstream:
      type: static
      url: http://product-service:8080
      
    plugins:
      - name: rate-limit
        config:
          requests_per_minute: 100
      
      - name: cache
        config:
          ttl: 60
```

### Global Configuration

```yaml
# config/gateway.yaml
gateway:
  # Server configuration
  server:
    http:
      enabled: true
      port: 8080
    https:
      enabled: true
      port: 8443
      cert: /etc/gateway/cert.pem
      key: /etc/gateway/key.pem
      tls_version: "1.3"
    http2:
      enabled: true
    
  # Worker configuration
  workers:
    count: auto  # auto-detect CPU cores
    max_connections: 10000
    
  # Connection settings
  upstream:
    timeout:
      connect: 5s
      read: 30s
      send: 30s
    keepalive:
      enabled: true
      max_connections: 100
      idle_timeout: 60s
    
  # Buffer settings
  buffer:
    request:
      max_size: 10mb
    response:
      max_size: 50mb
  
  # Logging
  logging:
    level: info
    format: json
    access_log:
      enabled: true
      path: /var/log/gateway/access.log
      fields:
        - timestamp
        - request_id
        - method
        - path
        - status
        - latency
        - client_ip
        - user_agent
    
  # Metrics
  metrics:
    enabled: true
    port: 9090
    path: /metrics
    
  # Tracing
  tracing:
    enabled: true
    sampler:
      type: probabilistic
      rate: 0.1  # 10% sampling
    exporter:
      type: jaeger
      endpoint: http://jaeger:14268/api/traces
```

---

## Data Models

### Route Model

```typescript
interface Route {
  id: string;
  name: string;
  hosts: string[];
  paths: PathMatcher[];
  methods: HttpMethod[];
  stripPath: boolean;
  preserveHost: boolean;
  upstream: UpstreamConfig;
  plugins: PluginConfig[];
  cors?: CorsConfig;
  createdAt: Date;
  updatedAt: Date;
}

interface PathMatcher {
  type: 'exact' | 'prefix' | 'regex';
  value: string;
}

interface UpstreamConfig {
  type: 'static' | 'service_discovery';
  url?: string;
  serviceName?: string;
  loadBalancer: LoadBalancerType;
  healthCheck?: HealthCheckConfig;
  fallback?: FallbackConfig;
}

type LoadBalancerType = 'round_robin' | 'least_conn' | 'ip_hash' | 'consistent_hash';

interface HealthCheckConfig {
  path: string;
  interval: number;  // seconds
  timeout: number;   // seconds
  healthyThreshold: number;
  unhealthyThreshold: number;
}
```

### Service Registry Model

```typescript
interface ServiceInstance {
  id: string;
  serviceName: string;
  host: string;
  port: number;
  protocol: 'http' | 'https';
  weight: number;
  metadata: Record<string, string>;
  healthStatus: HealthStatus;
  lastHealthCheck: Date;
  registeredAt: Date;
}

type HealthStatus = 'healthy' | 'unhealthy' | 'unknown';

interface Service {
  name: string;
  instances: ServiceInstance[];
  version: string;
  tags: string[];
}
```

---

## Design Patterns

| Pattern | Usage | Rationale |
|---------|-------|-----------|
| **Plugin Architecture** | Extensible middleware system | Allows custom functionality without core changes |
| **Chain of Responsibility** | Plugin execution order | Ordered, composable request/response processing |
| **Circuit Breaker** | Upstream failure handling | Prevents cascade failures |
| **Strategy** | Load balancing algorithms | Pluggable routing strategies |
| **Observer** | Configuration hot-reload | React to config changes without restart |
| **Connection Pool** | Upstream connections | Efficient connection reuse |
| **Object Pool** | Request/response objects | Reduce GC pressure under load |
| **Memoization** | Token validation cache | Avoid repeated JWT validation |

---

## Decision Log

1. **Decision**: [Key component design decision]
   - **Rationale**: [Why this decision was made]
   - **Impact**: [What it affects downstream]

---

*Document Version: 1.0*  
*Based on L2: API Gateway System Architecture*
