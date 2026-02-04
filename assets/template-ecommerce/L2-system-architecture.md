# L2 - System Architecture: E-Commerce Platform

## Overview

The e-commerce platform follows a microservices architecture with clear service boundaries aligned with business domains. Services communicate asynchronously via event-driven patterns to ensure loose coupling and high availability.

---

## Subsystems

### 1. User Service

**Responsibility**: Authentication, authorization, and user profile management

**Components**:
- Identity Provider (Auth0/Keycloak integration)
- User Profile Store
- Session Management
- MFA Provider

**Key Features**:
- JWT-based authentication
- Role-based access control (RBAC)
- Social login integration (Google, Facebook)
- Password reset and account recovery

**Data Stores**:
- PostgreSQL: User profiles and credentials
- Redis: Session cache

### 2. Product Catalog Service

**Responsibility**: Product information, categories, search, and inventory

**Components**:
- Product Management API
- Category Hierarchy Engine
- Search Engine (Elasticsearch)
- Inventory Tracker
- Image Processing Pipeline

**Key Features**:
- Full-text search with faceting
- Product variants (size, color, etc.)
- Inventory reservation during checkout
- Image optimization and CDN delivery

**Data Stores**:
- PostgreSQL: Product master data
- Elasticsearch: Search index
- S3: Product images
- Redis: Inventory cache

### 3. Order Service

**Responsibility**: Order lifecycle management from cart to fulfillment

**Components**:
- Shopping Cart Engine
- Checkout Orchestrator
- Order State Machine
- Pricing Engine
- Tax Calculator

**Key Features**:
- Guest and authenticated checkout
- Promotions and discounts
- Multi-currency support
- Order history and tracking

**Data Stores**:
- PostgreSQL: Order records
- Redis: Cart cache (TTL: 30 days)

### 4. Payment Gateway Service

**Responsibility**: Payment processing and financial transaction management

**Components**:
- Payment Orchestrator
- Gateway Adapters (Stripe, PayPal, Square)
- Fraud Detection Engine
- Refund Processor
- PCI Compliance Module

**Key Features**:
- Multi-gateway support with failover
- 3D Secure authentication
- Subscription billing
- Automated retry for failed payments

**Data Stores**:
- PostgreSQL: Transaction records
- Token vault for card data (PCI-compliant)

### 5. Notification Service

**Responsibility**: Email, SMS, and push notifications

**Components**:
- Template Engine
- Multi-channel Dispatcher
- Preference Manager
- Delivery Tracker

**Key Features**:
- Order confirmations and shipping updates
- Abandoned cart recovery
- Marketing campaigns
- Multi-language support

**Data Stores**:
- PostgreSQL: Notification history
- Template storage

### 6. Analytics Service

**Responsibility**: Business intelligence and reporting

**Components**:
- Event Collector
- Data Warehouse (Snowflake/BigQuery)
- Reporting Engine
- Dashboard Generator

**Key Features**:
- Real-time sales dashboard
- Conversion funnel analysis
- Inventory forecasting
- Merchant performance reports

**Data Stores**:
- Data warehouse
- Time-series database for metrics

### 7. API Gateway

**Responsibility**: Single entry point for all client requests

**Components**:
- Request Router
- Authentication Middleware
- Rate Limiter
- Request/Response Transformer
- Cache Layer

**Key Features**:
- API versioning
- Request throttling
- API key management
- Request/response logging

---

## System Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Web App    │  │  Mobile App  │  │  Admin Panel │  │  Partner API │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│                    (Routing, Auth, Rate Limiting)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│    USER SERVICE     │  │  PRODUCT CATALOG    │  │    ORDER SERVICE    │
│                     │  │                     │  │                     │
│ - Authentication    │  │ - Product CRUD      │  │ - Cart Management   │
│ - Authorization     │  │ - Search            │  │ - Checkout          │
│ - Profiles          │  │ - Inventory         │  │ - Order History     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   PAYMENT GATEWAY   │  │  NOTIFICATION SVC   │  │  ANALYTICS SERVICE  │
│                     │  │                     │  │                     │
│ - Payment Processing│  │ - Email             │  │ - Event Collection  │
│ - Fraud Detection   │  │ - SMS               │  │ - Reporting         │
│ - Subscriptions     │  │ - Push              │  │ - Dashboards        │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### Boundary Rules

1. **No Direct Database Access**: Services access only their own databases
2. **API-First Communication**: All inter-service communication via APIs
3. **Event-Driven Updates**: State changes published as events
4. **Synchronous for Queries**: Read operations via REST/GraphQL
5. **Asynchronous for Commands**: Write operations via message queue

---

## Data Flow

### Flow 1: User Registration

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  Client  │────▶│ API Gateway  │────▶│User Service │────▶│  Email   │
└──────────┘     └──────────────┘     └─────────────┘     └──────────┘
                                              │                   ▲
                                              │                   │
                                              ▼                   │
                                        ┌───────────┐             │
                                        │PostgreSQL │─────────────┘
                                        └───────────┘    Welcome Email
```

1. User submits registration form
2. API Gateway validates request format
3. User Service creates account
4. User Service publishes `user.created` event
5. Notification Service sends welcome email

### Flow 2: Product Search

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Client  │────▶│ API Gateway  │────▶│   Product   │────▶│Elasticsearch │
└──────────┘     └──────────────┘     │   Catalog   │     └──────────────┘
                                      └─────────────┘
```

1. User enters search query
2. API Gateway forwards to Product Catalog
3. Service queries Elasticsearch
4. Results returned with faceting options
5. Response cached for 5 minutes

### Flow 3: Checkout Process

```
┌─────────┐   ┌─────────────┐   ┌────────────┐   ┌──────────────┐   ┌──────────┐
│  Client │──▶│ API Gateway │──▶│   Order    │──▶│   Payment    │──▶│ External │
└─────────┘   └─────────────┘   │  Service   │   │   Gateway    │   │ Gateway  │
                                └────────────┘   └──────────────┘   └──────────┘
                                      │                                   │
                                      │              ┌────────────────────┘
                                      │              │  Payment Result
                                      │              ▼
                                      │         ┌──────────┐
                                      │         │ Order    │
                                      │         │ Service  │
                                      │         └──────────┘
                                      │              │
                                      │              ▼
                                      │         ┌──────────┐
                                      └────────▶│Notification
                                               │ Service  │
                                               └──────────┘
```

1. User proceeds to checkout
2. Order Service validates cart and inventory
3. Order Service calls Payment Gateway
4. Payment Gateway processes with external provider
5. Order Service updates order status
6. Notification Service sends confirmation

### Flow 4: Order Fulfillment (Async)

```
Order Service ──▶ Kafka ──▶ Inventory Service (reserve stock)
                     │
                     ├──▶ Notification Service (send confirmation)
                     │
                     ├──▶ Analytics Service (record transaction)
                     │
                     └──▶ Shipping Service (create shipment)
```

---

## Interfaces

### API Contracts

#### User Service API

```yaml
openapi: 3.0.0
paths:
  /api/v1/users/register:
    post:
      summary: Register new user
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: { type: string, format: email }
                password: { type: string, minLength: 8 }
                firstName: { type: string }
                lastName: { type: string }
      responses:
        201:
          description: User created
          content:
            application/json:
              schema:
                type: object
                properties:
                  userId: { type: string }
                  email: { type: string }
                  createdAt: { type: string, format: date-time }

  /api/v1/users/login:
    post:
      summary: Authenticate user
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: { type: string }
                password: { type: string }
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  accessToken: { type: string }
                  refreshToken: { type: string }
                  expiresIn: { type: integer }
```

#### Product Catalog API

```yaml
paths:
  /api/v1/products:
    get:
      summary: Search products
      parameters:
        - name: q
          in: query
          schema: { type: string }
        - name: category
          in: query
          schema: { type: string }
        - name: page
          in: query
          schema: { type: integer, default: 1 }
        - name: limit
          in: query
          schema: { type: integer, default: 20 }
      responses:
        200:
          description: Product list
          content:
            application/json:
              schema:
                type: object
                properties:
                  products:
                    type: array
                    items:
                      type: object
                      properties:
                        id: { type: string }
                        name: { type: string }
                        price: { type: number }
                        currency: { type: string }
                        imageUrl: { type: string }
                  total: { type: integer }
                  page: { type: integer }
                  totalPages: { type: integer }
```

#### Order Service API

```yaml
paths:
  /api/v1/orders:
    post:
      summary: Create order
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      productId: { type: string }
                      quantity: { type: integer, minimum: 1 }
                      variantId: { type: string }
                shippingAddress:
                  type: object
                  properties:
                    street: { type: string }
                    city: { type: string }
                    country: { type: string }
                    zipCode: { type: string }
                paymentMethodId: { type: string }
      responses:
        201:
          description: Order created
          content:
            application/json:
              schema:
                type: object
                properties:
                  orderId: { type: string }
                  status: { type: string, enum: [pending, confirmed, processing] }
                  totalAmount: { type: number }
                  currency: { type: string }
```

### Event Contracts

#### Event Schema

```protobuf
syntax = "proto3";

message UserCreated {
  string user_id = 1;
  string email = 2;
  string first_name = 3;
  string last_name = 4;
  int64 timestamp = 5;
}

message OrderPlaced {
  string order_id = 1;
  string user_id = 2;
  repeated OrderItem items = 3;
  Money total = 4;
  string status = 5;
  int64 timestamp = 6;
}

message OrderItem {
  string product_id = 1;
  string variant_id = 2;
  int32 quantity = 3;
  Money unit_price = 4;
}

message Money {
  string currency = 1;
  int64 amount_cents = 2;
}

message PaymentProcessed {
  string order_id = 1;
  string payment_id = 2;
  string status = 3;  // success, failed, pending
  int64 timestamp = 4;
}
```

#### Event Topics

| Topic | Publisher | Subscribers | Description |
|-------|-----------|-------------|-------------|
| `user.created` | User Service | Notification, Analytics | New user registration |
| `user.updated` | User Service | Analytics | Profile changes |
| `product.created` | Product Catalog | Search Index, Analytics | New product added |
| `product.updated` | Product Catalog | Search Index | Product changes |
| `product.inventory_changed` | Product Catalog | Order Service | Stock updates |
| `order.placed` | Order Service | Payment, Notification, Analytics | New order |
| `order.paid` | Payment Gateway | Order Service, Notification | Payment confirmed |
| `order.shipped` | Shipping Service | Notification, Analytics | Order shipped |

---

## Capacity Planning

| Subsystem | Initial | Year 1 | Year 3 | Scaling Strategy |
|-----------|---------|--------|--------|------------------|
| API Gateway | 2 instances | 4 | 8 | Horizontal |
| User Service | 2 instances | 3 | 6 | Horizontal |
| Product Catalog | 3 instances | 6 | 12 | Horizontal + Read Replicas |
| Order Service | 2 instances | 4 | 8 | Horizontal |
| Payment Gateway | 2 instances | 3 | 6 | Horizontal |
| PostgreSQL | db.r5.xlarge | db.r5.2xlarge | Sharded | Vertical + Sharding |
| Redis | cache.r5.large | cache.r5.xlarge | Cluster | Vertical + Clustering |
| Elasticsearch | 3 nodes | 5 nodes | 9 nodes | Horizontal |
| Kafka | 3 brokers | 5 brokers | 9 brokers | Horizontal |

---

*Document Version: 1.0*  
*Based on L1: E-Commerce Platform Meta-Architecture*
