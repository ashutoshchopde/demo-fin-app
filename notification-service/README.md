# Reporting & Analytics Service (Module F)

## Overview
Business intelligence and reporting service aggregating data from all other services.

## Dependencies
- **Direct**: Wallet Service (B), Payment Service (C), KYC/AML Service (E)
- **Indirect**: Auth Service (A) via ALL other services

## CASCADE VULNERABILITY
This service is the MOST VULNERABLE to cascading changes because it depends on:
1. Auth Service (A) - indirectly through B, C, E
2. Wallet Service (B) - directly for balance data
3. Payment Service (C) - directly for transaction data
4. KYC Service (E) - directly for compliance data

**Any change in ANY upstream service can break reports!**

## Example Cascade Scenarios

### Scenario 1: Auth Service adds `account_tier` field
**Cascade to Reporting**:
- Must update user activity reports
- Add tier-based analytics
- Modify financial summary to segment by tier

### Scenario 2: Wallet Service changes balance precision
**Cascade to Reporting**:
- Update balance aggregation logic
- Modify financial calculations
- Adjust decimal precision in reports

### Scenario 3: Payment Service adds new status
**Cascade to Reporting**:
- Update transaction status aggregations
- Add new status to charts
- Modify completion rate calculations

### Scenario 4: KYC Service changes verification levels
**Cascade to Reporting**:
- Update compliance reports
- Modify verified user counts
- Adjust risk categorization

## Features
- Transaction reports with aggregations
- User activity analytics
- Financial dashboards
- Compliance reports for regulators
- Data export (Excel, CSV, PDF)
- Scheduled reports

## API Endpoints
- GET /api/reports/transactions - Transaction analytics
- GET /api/reports/user-activity - User behavior patterns
- GET /api/reports/financial-summary - Financial KPIs
- GET /api/reports/compliance - Regulatory reports
- POST /api/reports/export - Export data

## Tech Stack
- Python, FastAPI
- PostgreSQL (cache)
- Elasticsearch (search & analytics)
- Pandas (data processing)
- Redis (report caching)

## Monitoring
Health check monitors ALL upstream services to detect cascade issues early.