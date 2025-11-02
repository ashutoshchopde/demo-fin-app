from fastapi import FastAPI, HTTPException, Depends, Header, status, BackgroundTasks
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
import uvicorn
from pydantic import BaseModel
import os
import uuid
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import enum
import httpx
import redis
import json

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
WALLET_SERVICE_URL = os.getenv("WALLET_SERVICE_URL", "http://localhost:8002")

# Database Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis Setup
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

app = FastAPI(title="Payment Processing Service", version="1.0.0")

# Enums
class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentType(str, enum.Enum):
    P2P = "p2p"
    MERCHANT = "merchant"
    BILL_PAYMENT = "bill_payment"
    WITHDRAWAL = "withdrawal"

# Database Models
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, index=True)  # UUID for idempotency
    from_wallet_id = Column(Integer, nullable=False)
    to_wallet_id = Column(Integer, nullable=False)
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String, default="USD")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    type = Column(SQLEnum(PaymentType), default=PaymentType.P2P)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class PaymentLog(Base):
    __tablename__ = "payment_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, index=True)
    status = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class PaymentRequest(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float
    currency: str = "USD"
    type: PaymentType = PaymentType.P2P
    description: Optional[str] = None
    idempotency_key: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    payment_id: str
    from_wallet_id: int
    to_wallet_id: int
    amount: float
    currency: str
    status: str
    type: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Verify user token
async def verify_user_token(authorization: str = Header(...)):
    """INDIRECT DEPENDENCY on Auth Service (Module A) via token validation"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/verify-token",
                headers={"Authorization": authorization}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

async def get_wallet_details(wallet_id: int, authorization: str):
    """
    DIRECT DEPENDENCY on Wallet Service (Module B)
    INDIRECT DEPENDENCY on Auth Service (Module A) through Wallet Service
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WALLET_SERVICE_URL}/api/wallet/{wallet_id}",
                headers={"Authorization": authorization}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
    except httpx.RequestError:
        return None

async def get_wallet_balance(wallet_id: int, authorization: str):
    """DIRECT DEPENDENCY on Wallet Service (Module B)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WALLET_SERVICE_URL}/api/wallet/{wallet_id}/balance",
                headers={"Authorization": authorization}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
    except httpx.RequestError:
        return None

async def check_user_kyc_status(user_id: int, authorization: str):
    """
    INDIRECT DEPENDENCY on Auth Service (Module A)
    Checks if user has completed KYC - cascaded requirement
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/user/{user_id}",
                headers={"Authorization": authorization}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get("kyc_status") == "verified"
            return False
    except httpx.RequestError:
        return False

def add_payment_log(db: Session, payment_id: str, status: str, message: str):
    log = PaymentLog(payment_id=payment_id, status=status, message=message)
    db.add(log)
    db.commit()

async def process_payment_async(payment_id: str, db: Session):
    """Background task to process payment"""
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    if not payment:
        return
    
    try:
        # Simulate payment processing
        payment.status = PaymentStatus.PROCESSING
        add_payment_log(db, payment_id, "processing", "Payment processing started")
        db.commit()
        
        # In production: Update wallet balances via Wallet Service API
        # This would involve calling Wallet Service to debit from_wallet and credit to_wallet
        
        # Mark as completed
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        add_payment_log(db, payment_id, "completed", "Payment completed successfully")
        db.commit()
        
        # Publish event to Kafka (for Notification Service)
        # kafka_producer.send('payment.completed', {
        #     'payment_id': payment_id,
        #     'amount': float(payment.amount),
        #     'from_wallet_id': payment.from_wallet_id,
        #     'to_wallet_id': payment.to_wallet_id
        # })
        
    except Exception as e:
        payment.status = PaymentStatus.FAILED
        add_payment_log(db, payment_id, "failed", str(e))
        db.commit()

# API Endpoints
@app.post("/api/payment/transfer", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_req: PaymentRequest,
    background_tasks: BackgroundTasks,
    user_data: dict = Depends(verify_user_token),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    # Check for idempotency
    if payment_req.idempotency_key:
        existing = db.query(Payment).filter(
            Payment.payment_id == payment_req.idempotency_key
        ).first()
        if existing:
            return existing
    
    # CRITICAL VALIDATION: Check sender's KYC status
    # This is CASCADED from Auth Service (Module A)
    sender_kyc_verified = await check_user_kyc_status(user_data["user_id"], authorization)
    if not sender_kyc_verified:
        raise HTTPException(
            status_code=403,
            detail="KYC verification required to send payments. This is a cascaded requirement from Auth Service."
        )
    
    # DEPENDENCY: Verify source wallet exists and belongs to user
    from_wallet = await get_wallet_details(payment_req.from_wallet_id, authorization)
    if not from_wallet:
        raise HTTPException(status_code=404, detail="Source wallet not found or access denied")
    
    # DEPENDENCY: Check if wallet is active (cascaded from Wallet Service changes)
    if from_wallet.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Source wallet is {from_wallet.get('status')}. Only active wallets can send payments."
        )
    
    # DEPENDENCY: Verify destination wallet exists
    to_wallet = await get_wallet_details(payment_req.to_wallet_id, authorization)
    if not to_wallet:
        raise HTTPException(status_code=404, detail="Destination wallet not found")
    
    # DEPENDENCY: Check balance
    balance_info = await get_wallet_balance(payment_req.from_wallet_id, authorization)
    if not balance_info or balance_info["balance"] < payment_req.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Currency match (DEPENDENCY on Wallet Service schema)
    if from_wallet["currency"] != payment_req.currency:
        raise HTTPException(status_code=400, detail="Currency mismatch with source wallet")
    
    # Create payment
    payment_id = payment_req.idempotency_key or str(uuid.uuid4())
    new_payment = Payment(
        payment_id=payment_id,
        from_wallet_id=payment_req.from_wallet_id,
        to_wallet_id=payment_req.to_wallet_id,
        amount=payment_req.amount,
        currency=payment_req.currency,
        type=payment_req.type,
        description=payment_req.description,
        status=PaymentStatus.PENDING
    )
    
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    add_payment_log(db, payment_id, "pending", "Payment created")
    
    # Process payment asynchronously
    background_tasks.add_task(process_payment_async, payment_id, db)
    
    return new_payment

@app.get("/api/payment/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    user_data: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment

@app.get("/api/payment/{payment_id}/status")
async def get_payment_status(
    payment_id: str,
    user_data: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    logs = db.query(PaymentLog).filter(
        PaymentLog.payment_id == payment_id
    ).order_by(PaymentLog.timestamp).all()
    
    return {
        "payment_id": payment_id,
        "status": payment.status,
        "logs": [{"status": log.status, "message": log.message, "timestamp": log.timestamp} for log in logs]
    }

@app.post("/api/payment/refund")
async def refund_payment(
    payment_id: str,
    user_data: dict = Depends(verify_user_token),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed payments can be refunded")
    
    # Verify ownership
    from_wallet = await get_wallet_details(payment.from_wallet_id, authorization)
    if not from_wallet:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payment.status = PaymentStatus.REFUNDED
    add_payment_log(db, payment_id, "refunded", "Payment refunded")
    db.commit()
    
    return {"message": "Payment refunded successfully", "payment_id": payment_id}

@app.get("/health")
async def health_check():
    # Check dependencies
    auth_healthy = False
    wallet_healthy = False
    
    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(f"{AUTH_SERVICE_URL}/health", timeout=2.0)
            auth_healthy = auth_response.status_code == 200
            
            wallet_response = await client.get(f"{WALLET_SERVICE_URL}/health", timeout=2.0)
            wallet_healthy = wallet_response.status_code == 200
    except:
        pass
    
    all_healthy = auth_healthy and wallet_healthy
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "payment-service",
        "dependencies": {
            "auth-service": "healthy" if auth_healthy else "unhealthy",
            "wallet-service": "healthy" if wallet_healthy else "unhealthy"
        },
        "cascade_info": {
            "direct_dependency": "Wallet Service (Module B)",
            "indirect_dependency": "Auth Service (Module A) via Wallet Service",
            "cascaded_validations": ["KYC status check", "Token validation", "Wallet status check"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", 8003)))