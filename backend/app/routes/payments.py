from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from ..models import User
from ..auth import get_current_user
from ..database import db
import stripe
import os
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["payments"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class DonationCreate(BaseModel):
    amount: int  # in cents
    message: Optional[str] = None
    stream_id: str

class SuperChatCreate(BaseModel):
    amount: int  # in cents
    message: str
    stream_id: str

@router.post("/donate")
async def create_donation(
    donation: DonationCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=donation.amount,
            currency="usd",
            metadata={
                "user_id": current_user.id,
                "stream_id": donation.stream_id,
                "type": "donation",
                "message": donation.message
            }
        )
        return {"client_secret": intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/super-chat")
async def create_super_chat(
    super_chat: SuperChatCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=super_chat.amount,
            currency="usd",
            metadata={
                "user_id": current_user.id,
                "stream_id": super_chat.stream_id,
                "type": "super_chat",
                "message": super_chat.message
            }
        )
        return {"client_secret": intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(payload: dict):
    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
        
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            metadata = payment_intent.metadata
            
            # Update stream stats based on payment type
            if metadata.get("type") == "super_chat":
                await db.store_chat_message(metadata["stream_id"], {
                    "type": "super_chat",
                    "username": metadata["user_id"],
                    "message": metadata["message"],
                    "amount": payment_intent.amount,
                    "timestamp": payment_intent.created
                })
            
            # Store payment in analytics
            await db.store_payment({
                "type": metadata["type"],
                "amount": payment_intent.amount,
                "user_id": metadata["user_id"],
                "stream_id": metadata["stream_id"],
                "timestamp": payment_intent.created
            })
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-subscription")
async def create_subscription(
    price_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        # Create a customer
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id}
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
        
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
