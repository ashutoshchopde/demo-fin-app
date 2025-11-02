# KYC/AML Service (Module E)

Processes KYC/AML (Know Your Customer / Anti-Money Laundering) compliance for users.

## Features
- Submit and track verification documents
- Updates user KYC status in Auth Service (reverse cascade)

## API Endpoints
- `POST /api/kyc/submit` — Submit documents for verification
- `GET /api/kyc/status/{user_id}` — Query KYC status for user

## Ports & Dependencies
- Runs on port `8005`
- Depends on: `auth-service` (for token, KYC status update)
