# Reporting & Analytics Service (Module F)

Aggregates and analyzes transactions for business requirements.

## Features
- Combine data from all services (esp. KYC, Wallet, Payment)
- Most cascade-vulnerable (for test/demos)

## API Endpoints
- `GET /api/reports/summary` — Aggregated summary (demo, extend as needed)
- (Add more for specifics)

## Ports & Dependencies
- Runs on port `8006`
- Depends on: wallet, payment, kyc, and indirectly auth
