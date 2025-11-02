# Payment Processing Service (Module C)

## Overview
Handles all payment transactions including P2P transfers, merchant payments, and refunds.

## Features
- Process payments between wallets
- P2P transfers
- Payment validation and status tracking
- Idempotency handling
- Async payment processing
- Transaction logs

## Dependencies
- **Direct**: Wallet Service (Module B)
- **Indirect**: Auth Service (Module A) via Wallet Service
- **Consumers**: Notification Service (Module D), KYC/AML Service (Module E), Reporting Service (Module F)

## Dependency Cascade Analysis

This is a CRITICAL module that demonstrates **indirect dependencies**:

### Direct Dependency on Wallet Service (B):
1. Fetches wallet details
2. Checks wallet balance
3. Verifies wallet status (active/frozen/closed)
4. Validates currency

### Indirect Dependency on Auth Service (A):
1. Token validation (through verify_user_token)
2. **KYC status check** - If Auth Service adds/changes kyc_status, this cascades here
3. User profile validation

### Example Cascade Scenarios:

**Scenario 1**: Auth Service (A) adds `kyc_status` field
- **Impact on Payment Service (C)**:
  - Must check KYC before processing payments
  - Add validation: `if not kyc_verified: raise HTTPException`
  - Update error messages
  - Cannot process payments for unverified users

**Scenario 2**: Wallet Service (B) adds `daily_limit` field
- **Impact on Payment Service (C)**:
  - Must check daily transaction limits
  - Track cumulative daily amounts
  - Add new validation logic
  - Update error handling

**Scenario 3**: Auth Service (A) changes JWT payload
- **Impact on Payment Service (C)** (indirect via Wallet):
  - Update token parsing logic
  - Modify user_data extraction
  - Update authorization header format

## Cascading Impact to Other Services

When Payment Service processes a payment:
1. **Notification Service (D)**: Receives payment events, sends notifications
2. **KYC/AML Service (E)**: Monitors for suspicious transactions
3. **Reporting Service (F)**: Includes payments in financial reports

## Tech Stack
- Python 3.11+
- FastAPI
- PostgreSQL
- Redis (idempotency, caching)
- Kafka (event streaming)
- httpx (service communication)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration
Update `.env`:
- DATABASE_URL
- AUTH_SERVICE_URL (Module A)
- WALLET_SERVICE_URL (Module B)
- KAFKA_BOOTSTRAP_SERVERS

## Running the Service

```bash
python main.py
```

Runs on port 8003.

## API Endpoints

All endpoints require JWT token:
`Authorization: Bearer <token>`

### Payment Operations
- `POST /api/payment/transfer` - Create payment (checks KYC, wallet status, balance)
- `GET /api/payment/{payment_id}` - Get payment details
- `GET /api/payment/{payment_id}/status` - Get payment status with logs
- `POST /api/payment/refund` - Refund a completed payment

### Health Check
- `GET /health` - Service health + ALL dependency statuses

## Database Schema

### payments table
- id (Primary Key)
- payment_id (UUID for idempotency)
- from_wallet_id (FK to Wallet Service)
- to_wallet_id (FK to Wallet Service)
- amount
- currency
- status (pending/processing/completed/failed/refunded)
- type (p2p/merchant/bill_payment/withdrawal)
- description
- created_at
- completed_at

### payment_logs table
- id (Primary Key)
- payment_id
- status
- message
- timestamp

## Critical Validations (Cascaded)

### From Auth Service (A):
✓ Token validation
✓ **KYC status check** - NEW, cascaded from Module A
✓ User authentication

### From Wallet Service (B):
✓ Wallet ownership verification
✓ Wallet status check (active/frozen/closed)
✓ Balance verification
✓ Currency validation

## Events Published
- `payment.created` - New payment initiated
- `payment.completed` - Payment successfully processed
- `payment.failed` - Payment failed
- `payment.refunded` - Payment refunded

These events are consumed by Notification and KYC/AML services.

## Events Consumed
- `wallet.status_changed` - Update payment processing based on wallet status
- `user.kyc_updated` - Update user payment limits

## Testing

```bash
# Create payment (requires verified KYC)
curl -X POST http://localhost:8003/api/payment/transfer \\
  -H "Authorization: Bearer <token>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "from_wallet_id": 1,
    "to_wallet_id": 2,
    "amount": 100.50,
    "currency": "USD",
    "type": "p2p",
    "description": "Test payment",
    "idempotency_key": "unique-key-123"
  }'

# Check payment status
curl -X GET http://localhost:8003/api/payment/unique-key-123/status \\
  -H "Authorization: Bearer <token>"
```

## Monitoring
- Health endpoint shows ALL upstream dependencies
- Metrics: payment success rate, processing time, failure reasons
- Alerts:
  - High failure rate
  - Wallet Service unavailable
  - Auth Service unavailable
  - KYC verification failures

## Circuit Breaker Pattern
Implements circuit breaker for both Auth and Wallet services:
- Opens after 5 consecutive failures
- Half-open state after 30 seconds
- Fallback: Queue payments for retry

## Production Impact Scenarios

### If Auth Service (A) changes:
1. Token format change → Update verify_user_token()
2. Add new user field → Update user validation logic
3. KYC status values change → Update KYC check logic

### If Wallet Service (B) changes:
1. Add wallet limits → Add limit validation
2. Change status enum → Update status checks
3. Add multi-currency → Update currency conversion logic

All changes cascade and require updates to this service!