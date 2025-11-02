# Wallet Service (Module B)

## Overview
Digital wallet and balance management service. Manages user wallets and transaction history.

## Features
- Wallet creation and management
- Balance inquiries with Redis caching
- Transaction history tracking
- Multi-currency support
- Wallet freeze/unfreeze operations

## Dependencies
- **Direct**: User Authentication Service (Module A)
- **Consumers**: Payment Processing Service (Module C), Reporting Service (Module F)

## Dependency Impact
This service is DIRECTLY dependent on Auth Service (Module A):
1. Uses Auth Service for token validation
2. Fetches user details including KYC status
3. **CRITICAL**: If Auth Service adds/changes user fields (like kyc_status), this service must be updated

### Example Cascade
When Auth Service adds `kyc_status` field:
- Wallet Service must validate KYC before creating wallets
- New validation logic: `kyc_status == "verified"` required
- Affects wallet creation API

## Tech Stack
- Python 3.11+
- FastAPI
- PostgreSQL
- Redis (caching)
- httpx (for Auth Service communication)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration
Update `.env`:
- DATABASE_URL
- AUTH_SERVICE_URL (Module A endpoint)
- REDIS_HOST

## Running the Service

```bash
python main.py
```

Runs on port 8002.

## API Endpoints

All endpoints require JWT token in Authorization header:
`Authorization: Bearer <token>`

### Wallet Management
- `POST /api/wallet/create` - Create new wallet (requires KYC verification)
- `GET /api/wallet/{wallet_id}` - Get wallet details
- `GET /api/wallet/user/{user_id}` - Get all user wallets
- `GET /api/wallet/{wallet_id}/balance` - Get current balance
- `PUT /api/wallet/{wallet_id}/status` - Update wallet status

### Transactions
- `GET /api/wallet/{wallet_id}/transactions` - Get transaction history

### Health Check
- `GET /health` - Service health + dependency status

## Database Schema

### wallets table
- id (Primary Key)
- user_id (Foreign Key to Auth Service)
- currency
- balance
- status (active/frozen/closed)
- created_at
- updated_at

### wallet_transactions table
- id (Primary Key)
- wallet_id (Foreign Key)
- type (credit/debit)
- amount
- balance_after
- reference_id
- description
- timestamp

## Cascade Scenarios

### Scenario 1: Auth Service changes user model
**Change**: Auth Service adds `kyc_status` field
**Impact on Wallet Service**:
- Update wallet creation to validate KYC
- Add KYC check: `if user['kyc_status'] != 'verified': raise HTTPException`
- Update error messages

### Scenario 2: Auth Service changes token format
**Change**: Auth Service changes JWT payload structure
**Impact on Wallet Service**:
- Update `verify_user_token()` function
- Modify user_data extraction logic

## Events Published
- `wallet.created` - New wallet created
- `wallet.status_changed` - Wallet status updated (affects Payment Service)

## Events Consumed
- `user.kyc_updated` - Update wallet restrictions based on KYC

## Testing

```bash
# Create wallet (requires valid JWT)
curl -X POST http://localhost:8002/api/wallet/create \\
  -H "Authorization: Bearer <token>" \\
  -H "Content-Type: application/json" \\
  -d '{"currency":"USD"}'

# Get balance
curl -X GET http://localhost:8002/api/wallet/1/balance \\
  -H "Authorization: Bearer <token>"
```

## Monitoring
- Health endpoint includes Auth Service status
- Metrics: wallet creation rate, balance queries, cache hit ratio
- Alerts: Auth Service unavailable, high error rate

## Circuit Breaker
Implements circuit breaker for Auth Service calls:
- Opens after 5 consecutive failures
- Half-open state after 30 seconds
- Graceful degradation when Auth Service is down