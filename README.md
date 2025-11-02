# FinFlow - Microservices Financial Platform

## 🏗️ Architecture Overview

This is a comprehensive financial application built with microservices architecture demonstrating **direct and indirect dependencies** between modules, and how changes cascade through the system.

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Kong/NGINX)                  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼──────────┐                    ┌──────────▼──────────┐
│  Module A (Core) │                    │   Module D          │
│  Auth Service    │◄───────────────────┤   Notification      │
│  Port: 8001      │                    │   Port: 8004        │
└────────┬─────────┘                    └─────────────────────┘
         │                                       ▲
         │                                       │
         │                              ┌────────┴────────┐
         │                              │    Kafka Events │
┌────────▼─────────┐                    └─────────────────┘
│  Module B        │                              ▲
│  Wallet Service  │                              │
│  Port: 8002      │                              │
└────────┬─────────┘                              │
         │                                        │
         │                                        │
┌────────▼─────────┐                    ┌─────────┴──────────┐
│  Module C        │───────────────────►│   Module E         │
│  Payment Service │                    │   KYC/AML Service  │
│  Port: 8003      │                    │   Port: 8005       │
└────────┬─────────┘                    └────────┬───────────┘
         │                                       │
         │                                       │
         └───────────────┬───────────────────────┘
                         │
                ┌────────▼─────────┐
                │   Module F       │
                │   Reporting      │
                │   Port: 8006     │
                └──────────────────┘
```

## 🔗 Dependency Chain

### Direct Dependencies
- **B → A**: Wallet Service depends on Auth Service
- **C → B**: Payment Service depends on Wallet Service
- **D → A, C**: Notification Service depends on Auth and Payment
- **E → A, C**: KYC/AML Service depends on Auth and Payment
- **F → B, C, E**: Reporting Service depends on Wallet, Payment, and KYC

### Indirect Dependencies
- **C → A**: Payment Service indirectly depends on Auth via Wallet
- **F → A**: Reporting Service indirectly depends on Auth via Wallet
- **D → B**: Notification Service indirectly depends on Wallet via Payment

## 📦 Modules

### Module A: User Authentication Service (Port 8001)
**Core Service - No Dependencies**

- User registration and login
- JWT token management
- User profile with KYC status
- Session management
- **Impact**: Changes here CASCADE to all other services!

**Example Cascade**: Adding `kyc_status` field:
```
Auth Service (A) adds kyc_status
    ↓
Wallet Service (B) validates KYC before wallet creation
    ↓
Payment Service (C) checks KYC before processing payments
    ↓
Reporting Service (F) includes KYC data in reports
```

### Module B: Wallet Service (Port 8002)
**Dependencies**: Auth Service (A)

- Digital wallet creation
- Balance management
- Multi-currency support
- Transaction history
- **Cascade Impact**: Wallet changes affect Payment and Reporting services

### Module C: Payment Processing Service (Port 8003)
**Direct**: Wallet Service (B)  
**Indirect**: Auth Service (A)

- P2P payments
- Payment processing with validation
- Idempotency handling
- Transaction status tracking
- **Cascade Complexity**: Most complex validation logic due to dependencies

### Module D: Notification Service (Port 8004)
**Dependencies**: Auth Service (A), Payment Service (C)

- Multi-channel notifications (Email, SMS, Push)
- Event-driven notification triggers
- Notification preferences
- **Cascade Source**: Listens to events from multiple services

### Module E: KYC/AML Compliance Service (Port 8005)
**Dependencies**: Auth Service (A), Payment Service (C)

- Document verification
- Risk scoring
- AML monitoring
- **Cascade Producer**: Updates KYC status in Auth Service → affects downstream

### Module F: Reporting & Analytics Service (Port 8006)
**Direct**: Wallet (B), Payment (C), KYC (E)  
**Indirect**: Auth Service (A) via all

- Transaction reports
- User analytics
- Financial dashboards
- Compliance reports
- **Cascade Vulnerability**: MOST affected by upstream changes

## 🔥 Cascade Impact Examples

### Example 1: Auth Service adds `account_tier` field

```
1. Auth Service (A) adds account_tier: ["bronze", "silver", "gold"]
   ↓
2. Wallet Service (B) must:
   - Add tier-based wallet limits
   - Update wallet creation logic
   ↓
3. Payment Service (C) must:
   - Check tier-based transaction limits
   - Add tier validation
   ↓
4. Reporting Service (F) must:
   - Add tier-based analytics
   - Update financial reports
```

**Production Impact**: Cannot determine directly in Auth Service, but affects production behavior of C and F!

### Example 2: Wallet Service changes balance precision

```
1. Wallet Service (B) changes balance from DECIMAL(10,2) to DECIMAL(20,4)
   ↓
2. Payment Service (C) must:
   - Update payment amount validation
   - Adjust decimal precision handling
   ↓
3. Reporting Service (F) must:
   - Update balance aggregation
   - Modify financial calculations
```

### Example 3: Payment Service adds new status "ON_HOLD"

```
1. Payment Service (C) adds PaymentStatus.ON_HOLD
   ↓
2. Notification Service (D) must:
   - Add notification template for ON_HOLD status
   ↓
3. Reporting Service (F) must:
   - Update status aggregations
   - Add ON_HOLD to charts
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- MongoDB 6+
- Redis 7+
- Kafka 3+ (optional, for events)
- Docker & Docker Compose (recommended)

### Installation

#### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

#### Option 2: Manual Setup

```bash
# Setup each service
cd auth-service
pip install -r requirements.txt
cp .env.example .env
# Configure .env
python main.py

# Repeat for each service
```

### Service URLs
- Auth Service: http://localhost:8001
- Wallet Service: http://localhost:8002
- Payment Service: http://localhost:8003
- Notification Service: http://localhost:8004
- KYC/AML Service: http://localhost:8005
- Reporting Service: http://localhost:8006

## 🧪 Testing Cascade Effects

### Test 1: Add KYC Status Field (Auth → Wallet → Payment)

```bash
# 1. Register user
curl -X POST http://localhost:8001/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User"
  }'

# 2. Login to get token
curl -X POST http://localhost:8001/api/auth/login \\
  -F "username=test@example.com" \\
  -F "password=password123"

# Save token as TOKEN

# 3. Try to create wallet (WILL FAIL - KYC not verified)
curl -X POST http://localhost:8002/api/wallet/create \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"currency": "USD"}'

# Expected: 403 - KYC verification required

# 4. Submit KYC
curl -X POST http://localhost:8005/api/kyc/submit \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": 1,
    "document_type": "passport",
    "document_url": "https://example.com/doc.pdf"
  }'

# This CASCADES: Updates kyc_status in Auth Service

# 5. Now create wallet (WILL SUCCEED)
curl -X POST http://localhost:8002/api/wallet/create \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"currency": "USD"}'

# Success! Cascade effect demonstrated
```

### Test 2: Wallet Status Change (Wallet → Payment)

```bash
# 1. Create payment (wallet is active - SUCCESS)
curl -X POST http://localhost:8003/api/payment/transfer \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "from_wallet_id": 1,
    "to_wallet_id": 2,
    "amount": 100.00,
    "currency": "USD"
  }'

# 2. Freeze wallet
curl -X PUT http://localhost:8002/api/wallet/1/status \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '"frozen"'

# 3. Try payment again (WILL FAIL - wallet frozen)
curl -X POST http://localhost:8003/api/payment/transfer \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "from_wallet_id": 1,
    "to_wallet_id": 2,
    "amount": 50.00,
    "currency": "USD"
  }'

# Expected: 400 - Source wallet is frozen

# Cascade demonstrated: Wallet status → Payment validation
```

## 📈 Monitoring Cascades

### Health Checks
Each service provides dependency health status:

```bash
# Check Payment Service (shows Auth + Wallet health)
curl http://localhost:8003/health

# Check Reporting Service (shows ALL dependencies)
curl http://localhost:8006/health
```

### Distributed Tracing
Use Jaeger to trace requests across services:

```bash
# Access Jaeger UI
http://localhost:16686

# Trace a payment request to see:
# Payment Service → Wallet Service → Auth Service
```

### Observability Stack
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Centralized logging

## 🔍 Understanding Cascade Detection

### Scenario: Cannot Determine Impact Directly

**Change**: Auth Service adds `account_tier` field

**Question**: How does this affect Payment Service?

**Answer**: 
1. **Direct Detection**: IMPOSSIBLE - Auth Service doesn't know about Payment Service
2. **Indirect Detection**: Through runtime errors or monitoring:
   - Payment Service tries to access wallet
   - Wallet Service changed its logic based on account_tier
   - Payment Service gets unexpected responses
   - Errors appear in production logs

**Solution**: 
- Contract testing between services
- Integration tests that exercise full chains
- Monitoring and alerting on cross-service failures
- Event-driven notifications of schema changes

## 🛠️ Development Guidelines

### Making Changes to Core Services

#### Auth Service (Module A) Changes
```
⚠️  CRITICAL: Changes cascade to ALL services!

Checklist:
☐ Update API contract documentation
☐ Notify all downstream teams
☐ Update Wallet Service validation
☐ Update Payment Service checks
☐ Update Reporting Service queries
☐ Run integration tests for all services
☐ Deploy in order: A → B → C → D,E → F
```

#### Wallet Service (Module B) Changes
```
⚠️  Affects: Payment Service, Reporting Service

Checklist:
☐ Update Payment Service balance checks
☐ Update Reporting Service aggregations
☐ Test payment flows end-to-end
☐ Deploy in order: B → C → F
```

### API Versioning
Use versioned endpoints to avoid breaking changes:
```
/api/v1/auth/login  (current)
/api/v2/auth/login  (new version with changes)
```

## 🏗️ Infrastructure

### Service Mesh (Istio)
- Traffic management
- Circuit breakers
- Retry policies
- Mutual TLS

### API Gateway (Kong)
- Rate limiting
- Authentication
- Request routing
- API versioning

### Event Bus (Kafka)
Topics:
- `user.created`
- `user.kyc_updated` ⚡ CASCADE TRIGGER
- `wallet.created`
- `wallet.status_changed` ⚡ CASCADE TRIGGER
- `payment.completed`
- `payment.failed`

## 📊 Production Deployment

### Blue-Green Deployment
For managing cascading updates:

```bash
# Deploy new version to "green" environment
deploy.sh --env green --service auth-service --version 2.0

# Test green environment
test.sh --env green

# Switch traffic to green
switch.sh --to green

# Keep blue as fallback
```

### Rollback Strategy
If cascade causes issues:

```bash
# Immediate rollback
rollback.sh --service payment-service --to previous

# Cascade rollback (if needed)
rollback.sh --cascade --from payment-service
```

## 📚 Documentation

Each service has comprehensive README with:
- Dependency details
- Cascade impact scenarios
- API documentation
- Testing guides

## 🤝 Contributing

When adding features:
1. Document all dependencies
2. List cascade impacts
3. Update integration tests
4. Notify dependent service teams

## 📝 License

MIT License

## 👥 Team

Built to demonstrate microservices cascade dependencies for learning and development purposes.

---

**Remember**: In production, changes to Module A can affect Module C even though there's no direct dependency. Always test the full dependency chain!
"""