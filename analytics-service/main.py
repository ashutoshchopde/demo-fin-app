"""
Reporting & Analytics Service (Module F)
Aggregates data from all services for analytics and reporting.
Most vulnerable to cascades!
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv
import httpx
import logging

load_dotenv()

SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8006))
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
WALLET_SERVICE_URL = os.getenv("WALLET_SERVICE_URL", "http://localhost:8002")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")
KYC_SERVICE_URL = os.getenv("KYC_SERVICE_URL", "http://localhost:8005")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Reporting & Analytics Service",
    description="Aggregates from all other services (most cascade-vulnerable)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_token(authorization: str = Header(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/verify-token",
                headers={"Authorization": authorization},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Auth error: {e}")
    raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/", tags=["Info"])
async def root():
    return {
        "service": "Reporting Service (Module F)",
        "version": "1.0.0",
        "direct_dependencies": ["Wallet (B)", "Payment (C)", "KYC (E)"],
        "indirect_dependencies": ["Auth (A) via Wallet"],
        "vulnerability": "CRITICAL - Affected by changes in ALL services"
    }

@app.get("/api/reports/summary", tags=["Reports"])
async def get_summary(user_data: dict = Depends(verify_token)):
    # Dummy summary for architecture skeleton
    # In real implementation, aggregate actual stats from each service
    now = datetime.utcnow().isoformat()
    return {
        "report_type": "financial_summary",
        "total_wallets": "(aggregate from Wallet Service)",
        "total_payments": "(aggregate from Payment Service)",
        "verified_users": "(aggregate from KYC Service/Auth)",
        "timestamp": now
    }

@app.get("/health", tags=["Health"])
async def health_check():
    services_status = {}
    services = [
        ("auth-service", AUTH_SERVICE_URL),
        ("wallet-service", WALLET_SERVICE_URL),
        ("payment-service", PAYMENT_SERVICE_URL),
        ("kyc-aml-service", KYC_SERVICE_URL),
    ]
    for name, url in services:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=2.0)
                services_status[name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_status[name] = "unhealthy"
    all_healthy = all(v == "healthy" for v in services_status.values())
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "reporting-analytics-service",
        "module": "F",
        "version": "1.0.0",
        "dependencies": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    logger.info(f"Starting Reporting Service on port {SERVICE_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
