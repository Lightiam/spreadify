from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os
from datetime import datetime

from ...db import get_db
from ...auth import get_current_user

router = APIRouter(prefix="/payments/paypal", tags=["payments"])

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if os.getenv("ENV") != "production" else "https://api-m.paypal.com"

async def get_paypal_access_token() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get PayPal access token")
        return response.json()["access_token"]

@router.post("/create-order")
async def create_paypal_order(
    amount: float,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal is not configured")

    access_token = await get_paypal_access_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "USD",
                            "value": str(amount)
                        }
                    }
                ]
            }
        )
        
        if response.status_code != 201:
            raise HTTPException(status_code=400, detail="Failed to create PayPal order")
            
        return response.json()

@router.post("/capture-order/{order_id}")
async def capture_paypal_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    access_token = await get_paypal_access_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )
        
        if response.status_code != 201:
            raise HTTPException(status_code=400, detail="Failed to capture PayPal payment")
            
        payment_data = response.json()
        
        # Store payment information
        payment = {
            "user_id": str(current_user.id),
            "provider": "paypal",
            "amount": float(payment_data["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]),
            "currency": payment_data["purchase_units"][0]["payments"]["captures"][0]["amount"]["currency_code"],
            "payment_id": payment_data["id"],
            "status": payment_data["status"],
            "created_at": datetime.utcnow()
        }
        
        # Add payment to database
        await db.store_payment(payment)
        
        return payment_data
