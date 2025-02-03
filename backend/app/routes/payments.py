from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import ChatMessage, Stream
import stripe
import os
from datetime import datetime
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
    db: Session = Depends(get_db)
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=donation.amount,
            currency="usd",
            metadata={
                "user_id": "anonymous",
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
    db: Session = Depends(get_db)
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=super_chat.amount,
            currency="usd",
            metadata={
                "user_id": "anonymous",
                "stream_id": super_chat.stream_id,
                "type": "super_chat",
                "message": super_chat.message
            }
        )
        return {"client_secret": intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    payload: dict,
    db: Session = Depends(get_db)
):
    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
        
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            metadata = payment_intent.metadata
            
            # Update stream stats based on payment type
            if metadata.get("type") == "super_chat":
                chat_message = {
                    "type": "super_chat",
                    "username": metadata.get("user_id"),
                    "message": metadata.get("message"),
                    "amount": payment_intent.get("amount"),
                    "timestamp": datetime.utcnow()
                }
                db.query(ChatMessage).filter(
                    ChatMessage.stream_id == metadata.get("stream_id")
                ).update(chat_message)
                db.commit()
            
            # Store payment in analytics
            payment = {
                "type": metadata.get("type"),
                "amount": payment_intent.get("amount"),
                "user_id": metadata.get("user_id"),
                "stream_id": metadata.get("stream_id"),
                "timestamp": datetime.utcnow()
            }
            db.add(payment)
            db.commit()
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-subscription")
async def create_subscription(
    price_id: str,
    db: Session = Depends(get_db)
):
    try:
        # Create a customer
        customer = stripe.Customer.create(
            email="dev@example.com",
            metadata={"user_id": "anonymous"}
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
