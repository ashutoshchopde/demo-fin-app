
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
import httpx
import pandas as pd

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
WALLET_SERVICE_URL = os.getenv("WALLET_SERVICE_URL")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL")
KYC_SERVICE_URL = os.getenv("KYC_SERVICE_URL")

app = FastAPI(title="Reporting & Analytics Service", version="1.0.0")

class ReportRequest(BaseModel):
    report_type: str
    start_date: datetime
    end_date: datetime
    filters: Optional[dict] = None

class ReportResponse(BaseModel):
    report_id: str
    report_type: str
    generated_at: datetime
    data: dict

async def verify_user_token(authorization: str = Header(...)):
    """INDIRECT DEPENDENCY on Auth Service (Module A)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/verify-token",
                headers={"Authorization": authorization}
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=401, detail="Invalid token")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.get("/api/reports/transactions")
async def get_transaction_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user_data: dict = Depends(verify_user_token),
    authorization: str = Header(...)
):
    """
    Generate transaction report
    DEPENDENCIES: Fetches data from Wallet, Payment, KYC services
    INDIRECT DEPENDENCY: All data cascades from Auth Service user changes
    """
    report_data = {
        "total_transactions": 0,
        "total_volume": 0,
        "by_status": {},
        "by_type": {},
        "generated_at": datetime.utcnow()
    }
    
    # In production: Aggregate data from Payment Service
    # This demonstrates indirect dependency on Auth Service:
    # - If Auth Service user schema changes, affects all services
    # - If Wallet Service balance calculation changes, affects reports
    # - If Payment Service status enum changes, breaks aggregation
    
    return {
        "report_type": "transactions",
        "period": {"start": start_date, "end": end_date},
        "data": report_data,
        "cascade_note": "This report aggregates data from multiple services. Any schema change in Auth, Wallet, or Payment services affects this report."
    }

@app.get("/api/reports/user-activity")
async def get_user_activity_report(
    user_id: Optional[int] = None,
    user_data: dict = Depends(verify_user_token),
    authorization: str = Header(...)
):
    """
    User activity report
    CASCADED from: Auth (user data), Wallet (balances), Payment (transactions), KYC (status)
    """
    activity_data = {}
    
    # Fetch from Auth Service
    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/user/{user_id or user_data['user_id']}",
                headers={"Authorization": authorization}
            )
            if user_response.status_code == 200:
                activity_data["user_info"] = user_response.json()
    except:
        pass
    
    # Fetch from Wallet Service
    try:
        async with httpx.AsyncClient() as client:
            wallet_response = await client.get(
                f"{WALLET_SERVICE_URL}/api/wallet/user/{user_id or user_data['user_id']}",
                headers={"Authorization": authorization}
            )
            if wallet_response.status_code == 200:
                activity_data["wallets"] = wallet_response.json()
    except:
        pass
    
    # Fetch from KYC Service
    try:
        async with httpx.AsyncClient() as client:
            kyc_response = await client.get(
                f"{KYC_SERVICE_URL}/api/kyc/status/{user_id or user_data['user_id']}",
                headers={"Authorization": authorization}
            )
            if kyc_response.status_code == 200:
                activity_data["kyc_status"] = kyc_response.json()
    except:
        pass
    
    return {
        "report_type": "user_activity",
        "user_id": user_id or user_data['user_id'],
        "data": activity_data,
        "dependencies_checked": ["Auth Service", "Wallet Service", "KYC Service"],
        "cascade_note": "Any field changes in upstream services require report schema updates"
    }

@app.get("/api/reports/financial-summary")
async def get_financial_summary(
    user_data: dict = Depends(verify_user_token),
    authorization: str = Header(...)
):
    """
    Financial summary dashboard
    MOST COMPLEX CASCADE: Depends on Auth, Wallet, Payment, KYC
    """
    summary = {
        "total_users": 0,
        "verified_users": 0,
        "total_wallets": 0,
        "total_balance": 0,
        "total_transactions": 0,
        "transaction_volume": 0,
        "generated_at": datetime.utcnow()
    }
    
    # In production: Aggregate from all services
    # CASCADE IMPACT EXAMPLE:
    # 1. Auth adds new user field → Update user count logic
    # 2. Wallet changes balance type → Update aggregation
    # 3. Payment adds new status → Update transaction counts
    # 4. KYC changes verification levels → Update verified_users logic
    
    return {
        "report_type": "financial_summary",
        "data": summary,
        "cascade_dependencies": {
            "direct": ["Wallet Service (B)", "Payment Service (C)", "KYC Service (E)"],
            "indirect": ["Auth Service (A) via Wallet, Payment, KYC"],
            "impact_note": "This report is affected by changes in ANY upstream service"
        }
    }

@app.get("/api/reports/compliance")
async def get_compliance_report(
    user_data: dict = Depends(verify_user_token),
    authorization: str = Header(...)
):
    """Compliance report for regulatory requirements"""
    return {
        "report_type": "compliance",
        "kyc_completion_rate": "85%",
        "high_risk_users": 12,
        "suspicious_transactions": 3,
        "generated_at": datetime.utcnow()
    }

@app.post("/api/reports/export")
async def export_report(
    report_request: ReportRequest,
    user_data: dict = Depends(verify_user_token)
):
    """Export report to Excel/CSV"""
    return {
        "message": "Report export initiated",
        "report_id": "RPT-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "format": "xlsx",
        "estimated_time": "2 minutes"
    }

@app.get("/health")
async def health_check():
    # Check ALL dependencies
    dependencies_status = {}
    
    for service_name, url in [
        ("auth-service", AUTH_SERVICE_URL),
        ("wallet-service", WALLET_SERVICE_URL),
        ("payment-service", PAYMENT_SERVICE_URL),
        ("kyc-service", KYC_SERVICE_URL)
    ]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=2.0)
                dependencies_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            dependencies_status[service_name] = "unhealthy"
    
    all_healthy = all(status == "healthy" for status in dependencies_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "reporting-analytics-service",
        "dependencies": dependencies_status,
        "cascade_info": {
            "direct_dependencies": ["Wallet (B)", "Payment (C)", "KYC (E)"],
            "indirect_dependencies": ["Auth (A) via all other services"],
            "impact_note": "Most vulnerable to cascading changes - depends on ALL services"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", 8006)))