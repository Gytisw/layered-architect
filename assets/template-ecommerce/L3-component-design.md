# L3 - Component Design: E-Commerce Platform

## Overview

This document provides detailed component-level design for each subsystem, including module breakdowns, API specifications, and dependency relationships.

---

## Module Breakdown

### 1. User Service Modules

```
user-service/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── User.ts
│   │   │   ├── Role.ts
│   │   │   └── Session.ts
│   │   ├── repositories/
│   │   │   ├── IUserRepository.ts
│   │   │   └── ISessionRepository.ts
│   │   └── services/
│   │       ├── IAuthService.ts
│   │       └── IUserService.ts
│   ├── application/
│   │   ├── commands/
│   │   │   ├── RegisterUser.ts
│   │   │   ├── LoginUser.ts
│   │   │   └── UpdateProfile.ts
│   │   ├── queries/
│   │   │   ├── GetUserById.ts
│   │   │   └── GetUserByEmail.ts
│   │   └── events/
│   │       └── UserEventHandlers.ts
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── UserRepository.ts
│   │   │   └── SessionRepository.ts
│   │   ├── auth/
│   │   │   ├── JwtAuthProvider.ts
│   │   │   ├── OAuthProvider.ts
│   │   │   └── MfaProvider.ts
│   │   └── messaging/
│   │       └── UserEventPublisher.ts
│   ├── interface/
│   │   ├── http/
│   │   │   ├── UserController.ts
│   │   │   ├── AuthController.ts
│   │   │   └── middleware/
│   │   │       ├── AuthMiddleware.ts
│   │   │       └── ValidationMiddleware.ts
│   │   └── dto/
│   │       ├── RegisterUserDto.ts
│   │       ├── UserResponseDto.ts
│   │       └── LoginDto.ts
│   └── app.ts
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

#### Module Descriptions

| Module | Responsibility | Design Pattern |
|--------|----------------|----------------|
| Domain Entities | Core business objects | DDD Entity |
| Domain Services | Business logic | Domain Service |
| Application Commands | Write operations | CQRS Command |
| Application Queries | Read operations | CQRS Query |
| Infrastructure Repositories | Data access | Repository Pattern |
| Interface Controllers | HTTP handling | MVC Controller |

### 2. Product Catalog Modules

```
product-catalog/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── Product.ts
│   │   │   ├── Category.ts
│   │   │   ├── Inventory.ts
│   │   │   └── ProductVariant.ts
│   │   ├── repositories/
│   │   │   ├── IProductRepository.ts
│   │   │   └── ICategoryRepository.ts
│   │   └── services/
│   │       ├── IInventoryService.ts
│   │       └── ISearchService.ts
│   ├── application/
│   │   ├── commands/
│   │   │   ├── CreateProduct.ts
│   │   │   ├── UpdateProduct.ts
│   │   │   └── UpdateInventory.ts
│   │   ├── queries/
│   │   │   ├── SearchProducts.ts
│   │   │   ├── GetProductById.ts
│   │   │   └── GetCategoryTree.ts
│   │   └── events/
│   │       ├── ProductEventHandlers.ts
│   │       └── InventoryEventHandlers.ts
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── ProductRepository.ts
│   │   │   └── CategoryRepository.ts
│   │   ├── search/
│   │   │   ├── ElasticsearchClient.ts
│   │   │   └── ProductSearchIndex.ts
│   │   ├── storage/
│   │   │   └── ImageStorage.ts
│   │   └── messaging/
│   │       └── ProductEventPublisher.ts
│   └── interface/
│       ├── http/
│       │   ├── ProductController.ts
│       │   ├── CategoryController.ts
│       │   └── SearchController.ts
│       └── dto/
│           ├── CreateProductDto.ts
│           ├── ProductResponseDto.ts
│           └── SearchRequestDto.ts
```

#### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Search Engine | Elasticsearch | Full-text search, faceting |
| Image Pipeline | Sharp/ImageMagick | Resize, optimize, convert |
| Image Storage | AWS S3 + CloudFront | Store and deliver images |
| Inventory Cache | Redis | Fast inventory lookups |

### 3. Order Service Modules

```
order-service/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── Order.ts
│   │   │   ├── OrderItem.ts
│   │   │   ├── Cart.ts
│   │   │   └── Payment.ts
│   │   ├── repositories/
│   │   │   ├── IOrderRepository.ts
│   │   │   └── ICartRepository.ts
│   │   ├── services/
│   │   │   ├── IOrderService.ts
│   │   │   ├── IPricingService.ts
│   │   │   └── ITaxService.ts
│   │   └── value-objects/
│   │       ├── Money.ts
│   │       ├── Address.ts
│   │       └── OrderStatus.ts
│   ├── application/
│   │   ├── commands/
│   │   │   ├── CreateOrder.ts
│   │   │   ├── UpdateOrderStatus.ts
│   │   │   ├── AddToCart.ts
│   │   │   └── Checkout.ts
│   │   ├── queries/
│   │   │   ├── GetOrderById.ts
│   │   │   ├── GetUserOrders.ts
│   │   │   └── GetCart.ts
│   │   ├── sagas/
│   │   │   └── CheckoutSaga.ts
│   │   └── events/
│   │       └── OrderEventHandlers.ts
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── OrderRepository.ts
│   │   │   └── CartRepository.ts
│   │   ├── pricing/
│   │   │   ├── PricingEngine.ts
│   │   │   └── PromotionCalculator.ts
│   │   ├── payment/
│   │   │   └── PaymentGatewayClient.ts
│   │   └── messaging/
│   │       └── OrderEventPublisher.ts
│   └── interface/
│       ├── http/
│       │   ├── OrderController.ts
│       │   └── CartController.ts
│       └── dto/
│           ├── CreateOrderDto.ts
│           ├── OrderResponseDto.ts
│           └── CheckoutDto.ts
```

#### Order State Machine

```
┌──────────┐    create    ┌──────────┐    confirm    ┌──────────┐
│  CART    │─────────────▶│ PENDING  │──────────────▶│CONFIRMED │
└──────────┘              └──────────┘               └──────────┘
                                                          │
                               ┌──────────────────────────┤
                               │                          │
                               ▼                          ▼
                         ┌──────────┐               ┌──────────┐
                         │ CANCELLED│               │PROCESSING│
                         └──────────┘               └──────────┘
                               ▲                          │
                               │                          │
                               │    ship                  │
                               └────────────────────┐     │
                                                    │     ▼
                                               ┌──────────┐
                                               │ SHIPPED  │
                                               └──────────┘
                                                    │
                                                    │ deliver
                                                    ▼
                                               ┌──────────┐
                                               │DELIVERED │
                                               └──────────┘
```

### 4. Payment Gateway Modules

```
payment-gateway/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── Transaction.ts
│   │   │   ├── PaymentMethod.ts
│   │   │   └── Refund.ts
│   │   ├── repositories/
│   │   │   └── ITransactionRepository.ts
│   │   └── services/
│   │       ├── IPaymentProcessor.ts
│   │       └── IFraudDetection.ts
│   ├── application/
│   │   ├── commands/
│   │   │   ├── ProcessPayment.ts
│   │   │   ├── RefundPayment.ts
│   │   │   └── StorePaymentMethod.ts
│   │   ├── queries/
│   │   │   ├── GetTransaction.ts
│   │   │   └── GetPaymentMethods.ts
│   │   └── events/
│   │       └── PaymentEventHandlers.ts
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   └── TransactionRepository.ts
│   │   ├── gateways/
│   │   │   ├── StripeAdapter.ts
│   │   │   ├── PayPalAdapter.ts
│   │   │   └── SquareAdapter.ts
│   │   ├── fraud/
│   │   │   └── FraudDetector.ts
│   │   └── vault/
│   │       └── TokenVault.ts
│   └── interface/
│       └── http/
│           └── PaymentController.ts
```

---

## API Contracts

### REST Endpoints

#### User Service

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/v1/users | Create user | Public |
| GET | /api/v1/users/:id | Get user by ID | Bearer |
| PUT | /api/v1/users/:id | Update user | Bearer |
| DELETE | /api/v1/users/:id | Delete user | Bearer |
| POST | /api/v1/auth/login | Login | Public |
| POST | /api/v1/auth/logout | Logout | Bearer |
| POST | /api/v1/auth/refresh | Refresh token | Bearer |
| POST | /api/v1/auth/mfa/enable | Enable MFA | Bearer |

#### Product Catalog

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/v1/products | List/search products | Public |
| GET | /api/v1/products/:id | Get product | Public |
| POST | /api/v1/products | Create product | Bearer (Admin) |
| PUT | /api/v1/products/:id | Update product | Bearer (Admin) |
| DELETE | /api/v1/products/:id | Delete product | Bearer (Admin) |
| GET | /api/v1/categories | List categories | Public |
| GET | /api/v1/products/:id/inventory | Get inventory | Bearer (Admin) |
| PUT | /api/v1/products/:id/inventory | Update inventory | Bearer (Admin) |

#### Order Service

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/v1/cart | Get current cart | Session/Bearer |
| POST | /api/v1/cart/items | Add item to cart | Session/Bearer |
| PUT | /api/v1/cart/items/:id | Update cart item | Session/Bearer |
| DELETE | /api/v1/cart/items/:id | Remove cart item | Session/Bearer |
| POST | /api/v1/orders | Create order | Bearer |
| GET | /api/v1/orders | List user orders | Bearer |
| GET | /api/v1/orders/:id | Get order details | Bearer |
| PUT | /api/v1/orders/:id/cancel | Cancel order | Bearer |
| GET | /api/v1/orders/:id/tracking | Track order | Bearer |

#### Payment Gateway

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/v1/payments | Process payment | Bearer (Internal) |
| GET | /api/v1/payments/:id | Get payment status | Bearer |
| POST | /api/v1/payments/:id/refund | Process refund | Bearer (Internal) |
| POST | /api/v1/payment-methods | Store payment method | Bearer |
| GET | /api/v1/payment-methods | List payment methods | Bearer |
| DELETE | /api/v1/payment-methods/:id | Remove payment method | Bearer |

### GraphQL Schema

```graphql
type User {
  id: ID!
  email: String!
  firstName: String!
  lastName: String!
  phone: String
  addresses: [Address!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Product {
  id: ID!
  name: String!
  description: String!
  sku: String!
  price: Money!
  compareAtPrice: Money
  categories: [Category!]!
  images: [Image!]!
  variants: [ProductVariant!]!
  inventory: Inventory!
  attributes: [Attribute!]!
  rating: Float
  reviewCount: Int
  isActive: Boolean!
}

type Order {
  id: ID!
  orderNumber: String!
  userId: ID!
  status: OrderStatus!
  items: [OrderItem!]!
  subtotal: Money!
  tax: Money!
  shipping: Money!
  discount: Money!
  total: Money!
  shippingAddress: Address!
  billingAddress: Address!
  payment: Payment!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Query {
  # User queries
  me: User!
  user(id: ID!): User
  
  # Product queries
  products(
    filter: ProductFilter
    sort: ProductSort
    pagination: PaginationInput
  ): ProductConnection!
  product(id: ID!): Product
  searchProducts(query: String!, filters: SearchFilters): ProductConnection!
  
  # Order queries
  orders(filter: OrderFilter, pagination: PaginationInput): OrderConnection!
  order(id: ID!): Order
  
  # Cart query
  cart: Cart
}

type Mutation {
  # Auth mutations
  register(input: RegisterInput!): AuthPayload!
  login(input: LoginInput!): AuthPayload!
  logout: Boolean!
  
  # Cart mutations
  addToCart(input: AddToCartInput!): Cart!
  updateCartItem(id: ID!, input: UpdateCartItemInput!): Cart!
  removeFromCart(id: ID!): Cart!
  
  # Order mutations
  createOrder(input: CreateOrderInput!): Order!
  cancelOrder(id: ID!): Order!
}
```

---

## Dependency Graph

### Service Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SERVICE DEPENDENCIES                           │
└─────────────────────────────────────────────────────────────────────────┘

API Gateway
│
├──▶ User Service
│    └──▶ PostgreSQL
│    └──▶ Redis (sessions)
│    └──▶ Kafka (events)
│
├──▶ Product Catalog
│    ├──▶ PostgreSQL
│    ├──▶ Elasticsearch
│    ├──▶ Redis (cache)
│    └──▶ Kafka (events)
│
├──▶ Order Service
│    ├──▶ PostgreSQL
│    ├──▶ Redis (carts)
│    ├──▶ Payment Gateway
│    └──▶ Kafka (events)
│
├──▶ Payment Gateway
│    ├──▶ PostgreSQL
│    ├──▶ Token Vault
│    ├──▶ External Gateways
│    └──▶ Kafka (events)
│
└──▶ Notification Service
     ├──▶ PostgreSQL
     ├──▶ Email Provider
     ├──▶ SMS Provider
     └──▶ Kafka (consumer)
```

### Internal Module Dependencies

```
Domain ◀──── Application ◀──── Infrastructure ◀──── Interface
 │                               │
 │                               └──▶ External Services
 │                                    (DB, Cache, Queue, etc.)
 │
 └──▶ No external dependencies
      (pure business logic)
```

---

## Data Models

### User Service

```typescript
// Domain Entities
interface User {
  id: string;
  email: string;
  passwordHash: string;
  firstName: string;
  lastName: string;
  phone?: string;
  roles: Role[];
  mfaEnabled: boolean;
  emailVerified: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface Session {
  id: string;
  userId: string;
  token: string;
  expiresAt: Date;
  createdAt: Date;
}

enum Role {
  CUSTOMER = 'customer',
  MERCHANT = 'merchant',
  ADMIN = 'admin'
}
```

### Product Catalog

```typescript
interface Product {
  id: string;
  name: string;
  description: string;
  sku: string;
  price: Money;
  compareAtPrice?: Money;
  categoryIds: string[];
  images: Image[];
  variants: ProductVariant[];
  attributes: Attribute[];
  seoTitle?: string;
  seoDescription?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface ProductVariant {
  id: string;
  sku: string;
  price: Money;
  options: VariantOption[];
  inventory: Inventory;
  image?: Image;
}

interface Inventory {
  quantity: number;
  reserved: number;
  available: number;
  lowStockThreshold: number;
}

interface Category {
  id: string;
  name: string;
  slug: string;
  parentId?: string;
  children: Category[];
  level: number;
}
```

### Order Service

```typescript
interface Order {
  id: string;
  orderNumber: string;
  userId: string;
  status: OrderStatus;
  items: OrderItem[];
  pricing: OrderPricing;
  shippingAddress: Address;
  billingAddress: Address;
  paymentId: string;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

interface OrderItem {
  id: string;
  productId: string;
  variantId?: string;
  name: string;
  sku: string;
  quantity: number;
  unitPrice: Money;
  totalPrice: Money;
  imageUrl?: string;
}

interface OrderPricing {
  subtotal: Money;
  tax: Money;
  shipping: Money;
  discount: Money;
  total: Money;
  currency: string;
}

enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}
```

---

## Design Patterns

| Pattern | Usage | Rationale |
|---------|-------|-----------|
| **Domain-Driven Design** | Core business logic organization | Aligns code with business domains |
| **CQRS** | Separating read and write operations | Optimizes for different access patterns |
| **Repository** | Data access abstraction | Enables testing, swappable implementations |
| **Saga** | Distributed transactions | Manages long-running business processes |
| **Event Sourcing** | Audit trail and state reconstruction | Complete history of changes |
| **Circuit Breaker** | External service calls | Prevents cascade failures |
| **Strategy** | Payment gateway selection | Pluggable payment providers |
| **Factory** | Complex object creation | Encapsulates creation logic |
| **Decorator** | Cross-cutting concerns (logging, metrics) | Clean separation of concerns |

---

*Document Version: 1.0*  
*Based on L2: E-Commerce Platform System Architecture*
