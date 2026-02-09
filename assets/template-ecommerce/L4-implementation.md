# L4 - Implementation: E-Commerce Platform

## Overview

This document provides implementation details, code patterns, and development guidelines for the e-commerce platform.

---

## File Structure

### Monorepo Layout

```
ecommerce-platform/
├── apps/
│   ├── api-gateway/              # API Gateway (Kong/Nginx)
│   ├── user-service/             # User management service
│   ├── product-catalog/          # Product catalog service
│   ├── order-service/            # Order processing service
│   ├── payment-gateway/          # Payment processing service
│   ├── notification-service/     # Email/SMS notifications
│   ├── analytics-service/        # Analytics and reporting
│   ├── web-frontend/             # Customer web app (Next.js)
│   └── admin-panel/              # Admin dashboard (React)
│
├── packages/
│   ├── shared/                   # Shared types and utilities
│   ├── ts-config/                # TypeScript configurations
│   ├── eslint-config/            # ESLint configurations
│   └── event-schemas/            # Kafka event schemas (Protobuf)
│
├── infra/
│   ├── terraform/                # Infrastructure as Code
│   ├── kubernetes/               # K8s manifests
│   ├── docker/                   # Docker configurations
│   └── scripts/                  # Deployment scripts
│
├── docs/
│   ├── architecture/             # Architecture Decision Records
│   ├── api/                      # API documentation
│   └── runbooks/                 # Operational runbooks
│
├── docker-compose.yml            # Local development
├── Makefile                      # Common tasks
└── turbo.json                    # Monorepo task runner
```

### Service Structure (per service)

```
apps/user-service/
├── src/
│   ├── config/                   # Configuration
│   │   ├── database.ts
│   │   ├── redis.ts
│   │   └── app.ts
│   ├── domain/                   # Domain layer
│   │   ├── entities/
│   │   ├── value-objects/
│   │   ├── repositories/
│   │   └── services/
│   ├── application/              # Application layer
│   │   ├── commands/
│   │   ├── queries/
│   │   ├── events/
│   │   └── dto/
│   ├── infrastructure/           # Infrastructure layer
│   │   ├── persistence/
│   │   ├── messaging/
│   │   ├── auth/
│   │   └── http/
│   ├── interface/                # Interface layer
│   │   ├── http/
│   │   └── middleware/
│   ├── utils/                    # Utilities
│   └── app.ts                    # Application entry
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── Dockerfile
├── package.json
└── tsconfig.json
```

---

## Code Patterns

### 1. Domain Entity Pattern

```typescript
// src/domain/entities/User.ts
import { Entity } from '../../shared/Entity';
import { Result } from '../../shared/Result';

interface UserProps {
  email: string;
  passwordHash: string;
  firstName: string;
  lastName: string;
  phone?: string;
  roles: Role[];
  mfaEnabled: boolean;
  emailVerified: boolean;
}

export class User extends Entity<UserProps> {
  private constructor(props: UserProps, id?: string) {
    super(props, id);
  }

  static create(props: UserProps, id?: string): Result<User> {
    if (!props.email || !props.email.includes('@')) {
      return Result.fail<User>('Invalid email address');
    }
    
    if (!props.firstName || props.firstName.length < 2) {
      return Result.fail<User>('First name must be at least 2 characters');
    }

    return Result.ok(new User(props, id));
  }

  get email(): string {
    return this.props.email;
  }

  get fullName(): string {
    return `${this.props.firstName} ${this.props.lastName}`;
  }

  verifyEmail(): void {
    this.props.emailVerified = true;
    this.markUpdated();
  }

  enableMfa(): void {
    this.props.mfaEnabled = true;
    this.markUpdated();
  }

  hasRole(role: Role): boolean {
    return this.props.roles.includes(role);
  }
}
```

### 2. Repository Pattern

```typescript
// src/domain/repositories/IUserRepository.ts
import { User } from '../entities/User';

export interface IUserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<void>;
  delete(id: string): Promise<void>;
  exists(email: string): Promise<boolean>;
}

// src/infrastructure/persistence/UserRepository.ts
import { IUserRepository } from '../../domain/repositories/IUserRepository';
import { User } from '../../domain/entities/User';
import { PrismaClient } from '@prisma/client';

export class UserRepository implements IUserRepository {
  constructor(private prisma: PrismaClient) {}

  async findById(id: string): Promise<User | null> {
    const data = await this.prisma.user.findUnique({ where: { id } });
    if (!data) return null;
    
    return this.toDomain(data);
  }

  async findByEmail(email: string): Promise<User | null> {
    const data = await this.prisma.user.findUnique({ where: { email } });
    if (!data) return null;
    
    return this.toDomain(data);
  }

  async save(user: User): Promise<void> {
    const data = this.toPersistence(user);
    
    await this.prisma.user.upsert({
      where: { id: user.id },
      create: data,
      update: data,
    });
  }

  async delete(id: string): Promise<void> {
    await this.prisma.user.delete({ where: { id } });
  }

  async exists(email: string): Promise<boolean> {
    const count = await this.prisma.user.count({ where: { email } });
    return count > 0;
  }

  private toDomain(data: any): User {
    const result = User.create({
      email: data.email,
      passwordHash: data.passwordHash,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      roles: data.roles,
      mfaEnabled: data.mfaEnabled,
      emailVerified: data.emailVerified,
    }, data.id);

    if (result.isFailure) {
      throw new Error(`Failed to restore user: ${result.error}`);
    }

    return result.getValue();
  }

  private toPersistence(user: User): any {
    return {
      id: user.id,
      email: user.email,
      passwordHash: user.passwordHash,
      firstName: user.firstName,
      lastName: user.lastName,
      phone: user.phone,
      roles: user.roles,
      mfaEnabled: user.mfaEnabled,
      emailVerified: user.emailVerified,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
    };
  }
}
```

### 3. CQRS Command Pattern

```typescript
// src/application/commands/RegisterUser.ts
import { IUserRepository } from '../../domain/repositories/IUserRepository';
import { IEventPublisher } from '../../domain/events/IEventPublisher';
import { User } from '../../domain/entities/User';
import { PasswordService } from '../../domain/services/PasswordService';
import { UserCreatedEvent } from '../../domain/events/UserCreatedEvent';

interface RegisterUserRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

interface RegisterUserResponse {
  userId: string;
  email: string;
  createdAt: Date;
}

export class RegisterUserHandler {
  constructor(
    private userRepository: IUserRepository,
    private eventPublisher: IEventPublisher,
    private passwordService: PasswordService,
  ) {}

  async execute(request: RegisterUserRequest): Promise<RegisterUserResponse> {
    // Check if user exists
    const exists = await this.userRepository.exists(request.email);
    if (exists) {
      throw new Error('User with this email already exists');
    }

    // Hash password
    const passwordHash = await this.passwordService.hash(request.password);

    // Create user entity
    const userResult = User.create({
      email: request.email,
      passwordHash,
      firstName: request.firstName,
      lastName: request.lastName,
      roles: ['customer'],
      mfaEnabled: false,
      emailVerified: false,
    });

    if (userResult.isFailure) {
      throw new Error(userResult.error);
    }

    const user = userResult.getValue();

    // Save to database
    await this.userRepository.save(user);

    // Publish event
    await this.eventPublisher.publish(new UserCreatedEvent({
      userId: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
    }));

    return {
      userId: user.id,
      email: user.email,
      createdAt: user.createdAt,
    };
  }
}
```

### 4. CQRS Query Pattern

```typescript
// src/application/queries/GetUserById.ts
import { IUserReadRepository } from '../repositories/IUserReadRepository';

interface GetUserByIdRequest {
  userId: string;
}

interface GetUserByIdResponse {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  roles: string[];
  createdAt: Date;
}

export class GetUserByIdHandler {
  constructor(private readRepository: IUserReadRepository) {}

  async execute(request: GetUserByIdRequest): Promise<GetUserByIdResponse | null> {
    const user = await this.readRepository.findById(request.userId);
    
    if (!user) {
      return null;
    }

    return {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      fullName: `${user.firstName} ${user.lastName}`,
      roles: user.roles,
      createdAt: user.createdAt,
    };
  }
}
```

### 5. Saga Pattern for Distributed Transactions

```typescript
// src/application/sagas/CheckoutSaga.ts
import { Saga } from '../../shared/Saga';
import { OrderService } from '../services/OrderService';
import { PaymentService } from '../services/PaymentService';
import { InventoryService } from '../services/InventoryService';

interface CheckoutContext {
  orderId: string;
  userId: string;
  items: OrderItem[];
  total: Money;
  paymentMethodId: string;
}

export class CheckoutSaga extends Saga<CheckoutContext> {
  constructor(
    private orderService: OrderService,
    private paymentService: PaymentService,
    private inventoryService: InventoryService,
  ) {
    super();
  }

  async execute(context: CheckoutContext): Promise<void> {
    try {
      // Step 1: Reserve inventory
      this.addStep('reserveInventory', async () => {
        await this.inventoryService.reserveItems(context.orderId, context.items);
      }, async () => {
        await this.inventoryService.releaseReservation(context.orderId);
      });

      // Step 2: Create payment
      this.addStep('processPayment', async () => {
        const payment = await this.paymentService.charge({
          orderId: context.orderId,
          amount: context.total,
          paymentMethodId: context.paymentMethodId,
        });
        context.paymentId = payment.id;
      }, async () => {
        if (context.paymentId) {
          await this.paymentService.refund(context.paymentId);
        }
      });

      // Step 3: Confirm order
      this.addStep('confirmOrder', async () => {
        await this.orderService.confirmOrder(context.orderId, context.paymentId);
      });

      // Step 4: Commit inventory
      this.addStep('commitInventory', async () => {
        await this.inventoryService.commitReservation(context.orderId);
      });

      await this.run();
    } catch (error) {
      // Compensating transactions are automatically executed
      throw new CheckoutFailedError('Checkout failed', error);
    }
  }
}
```

### 6. Middleware Pattern

```typescript
// src/interface/middleware/AuthMiddleware.ts
import { Request, Response, NextFunction } from 'express';
import { JwtAuthProvider } from '../../infrastructure/auth/JwtAuthProvider';

export interface AuthenticatedRequest extends Request {
  user?: {
    userId: string;
    email: string;
    roles: string[];
  };
}

export const authMiddleware = (
  authProvider: JwtAuthProvider,
  requiredRoles?: string[]
) => {
  return async (
    req: AuthenticatedRequest,
    res: Response,
    next: NextFunction
  ) => {
    try {
      const authHeader = req.headers.authorization;
      
      if (!authHeader?.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or invalid authorization header' });
      }

      const token = authHeader.substring(7);
      const decoded = await authProvider.verifyToken(token);

      if (requiredRoles && requiredRoles.length > 0) {
        const hasRole = requiredRoles.some(role => decoded.roles.includes(role));
        if (!hasRole) {
          return res.status(403).json({ error: 'Insufficient permissions' });
        }
      }

      req.user = decoded;
      next();
    } catch (error) {
      return res.status(401).json({ error: 'Invalid token' });
    }
  };
};

// src/interface/middleware/RateLimitMiddleware.ts
import rateLimit from 'express-rate-limit';
import Redis from 'ioredis';

export const createRateLimitMiddleware = (redis: Redis) => {
  return rateLimit({
    store: new RedisStore({
      client: redis,
      prefix: 'rl:',
    }),
    windowMs: 60 * 1000, // 1 minute
    max: (req) => {
      // Authenticated users get higher limits
      return req.user ? 1000 : 100;
    },
    keyGenerator: (req) => {
      return req.user?.userId || req.ip;
    },
    handler: (req, res) => {
      res.status(429).json({
        error: 'Too many requests',
        retryAfter: Math.ceil(req.rateLimit.resetTime.getTime() / 1000),
      });
    },
  });
};
```

### 7. Event Publisher Pattern

```typescript
// src/infrastructure/messaging/KafkaEventPublisher.ts
import { Kafka, Producer } from 'kafkajs';
import { IEventPublisher } from '../../domain/events/IEventPublisher';
import { DomainEvent } from '../../domain/events/DomainEvent';

export class KafkaEventPublisher implements IEventPublisher {
  private producer: Producer;

  constructor(private kafka: Kafka) {
    this.producer = this.kafka.producer();
  }

  async connect(): Promise<void> {
    await this.producer.connect();
  }

  async disconnect(): Promise<void> {
    await this.producer.disconnect();
  }

  async publish<T>(event: DomainEvent<T>): Promise<void> {
    const topic = this.getTopicForEvent(event);
    
    await this.producer.send({
      topic,
      messages: [
        {
          key: event.aggregateId,
          value: JSON.stringify({
            type: event.type,
            payload: event.payload,
            timestamp: event.timestamp,
            correlationId: event.correlationId,
          }),
          headers: {
            'event-type': event.type,
            'event-version': event.version,
          },
        },
      ],
    });
  }

  async publishBatch(events: DomainEvent<any>[]): Promise<void> {
    const messagesByTopic = new Map<string, any[]>();

    for (const event of events) {
      const topic = this.getTopicForEvent(event);
      const messages = messagesByTopic.get(topic) || [];
      messages.push({
        key: event.aggregateId,
        value: JSON.stringify(event),
      });
      messagesByTopic.set(topic, messages);
    }

    for (const [topic, messages] of messagesByTopic) {
      await this.producer.send({ topic, messages });
    }
  }

  private getTopicForEvent(event: DomainEvent<any>): string {
    // Topic naming convention: {service}.{entity}.{action}
    // e.g., user-service.user.created
    return event.type.replace(/\./g, '-');
  }
}
```

---

## Implementation Details

### Database Schema (Prisma)

```prisma
// apps/user-service/prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id              String   @id @default(uuid())
  email           String   @unique
  passwordHash    String
  firstName       String
  lastName        String
  phone           String?
  roles           String[] @default(["customer"])
  mfaEnabled      Boolean  @default(false)
  mfaSecret       String?
  emailVerified   Boolean  @default(false)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@index([email])
  @@map("users")
}

model Session {
  id        String   @id @default(uuid())
  userId    String
  token     String   @unique
  expiresAt DateTime
  createdAt DateTime @default(now())
  
  @@index([userId])
  @@index([token])
  @@map("sessions")
}
```

### Docker Configuration

```dockerfile
# apps/user-service/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Generate Prisma client
RUN npx prisma generate

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install production dependencies only
RUN npm ci --only=production

# Generate Prisma client for production
RUN npx prisma generate

# Copy built application
COPY --from=builder /app/dist ./dist

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["node", "dist/app.js"]
```

### Kubernetes Deployment

```yaml
# infra/kubernetes/user-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: ecommerce
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
        - name: user-service
          image: ecommerce/user-service:latest
          ports:
            - containerPort: 3000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: user-service-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: user-service-secrets
                  key: redis-url
            - name: KAFKA_BROKERS
              value: "kafka:9092"
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: user-service-secrets
                  key: jwt-secret
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
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Environment Configuration

```typescript
// src/config/app.ts
import { config } from 'dotenv';
config();

interface AppConfig {
  env: 'development' | 'production' | 'test';
  port: number;
  database: {
    url: string;
    poolSize: number;
  };
  redis: {
    url: string;
    ttl: number;
  };
  kafka: {
    brokers: string[];
    clientId: string;
    groupId: string;
  };
  jwt: {
    secret: string;
    expiresIn: string;
  };
  logLevel: string;
}

export const appConfig: AppConfig = {
  env: (process.env.NODE_ENV as any) || 'development',
  port: parseInt(process.env.PORT || '3000', 10),
  database: {
    url: process.env.DATABASE_URL || 'postgresql://localhost:5432/ecommerce',
    poolSize: parseInt(process.env.DATABASE_POOL_SIZE || '10', 10),
  },
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
    ttl: parseInt(process.env.REDIS_TTL || '3600', 10),
  },
  kafka: {
    brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(','),
    clientId: process.env.KAFKA_CLIENT_ID || 'user-service',
    groupId: process.env.KAFKA_GROUP_ID || 'user-service-group',
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'dev-secret',
    expiresIn: process.env.JWT_EXPIRES_IN || '24h',
  },
  logLevel: process.env.LOG_LEVEL || 'info',
};
```

---

## Testing Strategy

### Unit Test Example

```typescript
// tests/unit/domain/entities/User.test.ts
import { User } from '../../../src/domain/entities/User';

describe('User Entity', () => {
  describe('create', () => {
    it('should create a valid user', () => {
      const result = User.create({
        email: 'test@example.com',
        passwordHash: 'hashedpassword',
        firstName: 'John',
        lastName: 'Doe',
        roles: ['customer'],
        mfaEnabled: false,
        emailVerified: false,
      });

      expect(result.isSuccess).toBe(true);
      expect(result.getValue().email).toBe('test@example.com');
    });

    it('should fail with invalid email', () => {
      const result = User.create({
        email: 'invalid-email',
        passwordHash: 'hashedpassword',
        firstName: 'John',
        lastName: 'Doe',
        roles: ['customer'],
        mfaEnabled: false,
        emailVerified: false,
      });

      expect(result.isFailure).toBe(true);
      expect(result.error).toContain('Invalid email');
    });
  });

  describe('verifyEmail', () => {
    it('should mark email as verified', () => {
      const result = User.create({
        email: 'test@example.com',
        passwordHash: 'hashedpassword',
        firstName: 'John',
        lastName: 'Doe',
        roles: ['customer'],
        mfaEnabled: false,
        emailVerified: false,
      });

      const user = result.getValue();
      user.verifyEmail();

      expect(user.emailVerified).toBe(true);
    });
  });
});
```

### Integration Test Example

```typescript
// tests/integration/infrastructure/persistence/UserRepository.test.ts
import { UserRepository } from '../../../src/infrastructure/persistence/UserRepository';
import { PrismaClient } from '@prisma/client';
import { User } from '../../../src/domain/entities/User';

describe('UserRepository Integration', () => {
  let prisma: PrismaClient;
  let repository: UserRepository;

  beforeAll(async () => {
    prisma = new PrismaClient();
    repository = new UserRepository(prisma);
    await prisma.$connect();
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    await prisma.user.deleteMany();
  });

  describe('save', () => {
    it('should save and retrieve a user', async () => {
      const userResult = User.create({
        email: 'test@example.com',
        passwordHash: 'hashedpassword',
        firstName: 'John',
        lastName: 'Doe',
        roles: ['customer'],
        mfaEnabled: false,
        emailVerified: false,
      });

      const user = userResult.getValue();
      await repository.save(user);

      const retrieved = await repository.findById(user.id);
      expect(retrieved).not.toBeNull();
      expect(retrieved?.email).toBe('test@example.com');
    });
  });
});
```

---

## Deployment Pipeline

```yaml
# .github/workflows/user-service.yml
name: User Service CI/CD

on:
  push:
    paths:
      - 'apps/user-service/**'
      - 'packages/shared/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint --workspace=apps/user-service
      
      - name: Unit tests
        run: npm run test:unit --workspace=apps/user-service
      
      - name: Integration tests
        run: npm run test:integration --workspace=apps/user-service
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t ecommerce/user-service:${{ github.sha }} \
            -f apps/user-service/Dockerfile \
            apps/user-service
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ecommerce/user-service:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/user-service \
            user-service=ecommerce/user-service:${{ github.sha }} \
            -n ecommerce
          kubectl rollout status deployment/user-service -n ecommerce
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
*Based on L3: E-Commerce Platform Component Design*
