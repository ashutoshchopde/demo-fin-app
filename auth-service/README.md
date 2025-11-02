# User Authentication Service (Module A)

## Overview
Core authentication and user management service. This is the foundational service that all other services depend on.

## Features
- User registration and login
- JWT token generation and validation
- User profile management
- Role-based access control (RBAC)
- Session management with Redis
- KYC status tracking

## Dependencies
- **Direct**: None (Core Service)
- **Consumers**: Wallet Service, Payment Service, Notification Service, KYC/AML Service, Reporting Service

## Tech Stack
- Python 3.11+
- FastAPI
- PostgreSQL
- Redis
- JWT
- SQLAlchemy

## Installation

```bash
pip install -r requirements.txt
```

## Configuration
Copy `.env.example` to `.env` and configure:
- DATABASE_URL
- REDIS_HOST and REDIS_PORT
- SECRET_KEY (change in production!)

## Running the Service

```bash
python main.py
```

The service will run on port 8001.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify-token` - Verify JWT token

### User Management
- `GET /api/auth/user/{user_id}` - Get user details
- `PUT /api/auth/user/{user_id}` - Update user profile

### Health Check
- `GET /health` - Service health status

## Database Schema

### users table
- id (Primary Key)
- email (Unique)
- password_hash
- name
- phone
- role
- is_active
- kyc_status (NEW: Cascades to other services)
- created_at
- updated_at

### sessions (Redis)
- session:{user_id}:{token} -> "active"
- blacklist:{token} -> "true"

## Cascade Impact Example

When `kyc_status` field is updated:
1. **Direct Impact**: Wallet Service validates KYC before wallet creation
2. **Indirect Impact**: 
   - Payment Service checks KYC before processing payments
   - Notification Service sends KYC status alerts
   - Reporting Service includes KYC data in reports

## Events Published
- `user.created` - When new user registers
- `user.kyc_updated` - When KYC status changes (CRITICAL for cascading)

## Docker Support

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Testing

```bash
# Test registration
curl -X POST http://localhost:8001/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Test login
curl -X POST http://localhost:8001/api/auth/login \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=test@example.com&password=password123"
```

## Monitoring
- Prometheus metrics exposed at `/metrics`
- Logs sent to centralized logging system
- Health check at `/health`
