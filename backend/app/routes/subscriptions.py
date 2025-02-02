from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from ..models import User, Channel
from ..auth import get_current_user
from ..database import db
import stripe
import os
from pydantic import BaseModel
from datetime import datetime
from stripe.stripe_object import StripeObject

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class SubscriptionCreate(BaseModel):
    channel_id: str

@router.post("")
async def create_subscription(
    subscription: SubscriptionCreate,
    current_user: User = Depends(get_current_user)
):
    # Get channel
    channel = await db.get_channel(subscription.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    if not channel.settings.monetization_enabled:
        raise HTTPException(
            status_code=400,
            detail="Channel monetization is not enabled"
        )
        
    if not channel.settings.subscription_price:
        raise HTTPException(
            status_code=400,
            detail="Channel subscription price is not set"
        )
    
    try:
        # Create Stripe customer if not exists
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id}
        )
        
        # Create subscription
        stripe_subscription: StripeObject = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": channel.settings.subscription_price}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
            metadata={
                "channel_id": channel.id,
                "subscriber_id": current_user.id
            }
        )
        
        # Store subscription in database
        await db.create_subscription({
            "id": stripe_subscription.id,
            "channel_id": channel.id,
            "subscriber_id": current_user.id,
            "status": stripe_subscription.status,
            "created_at": datetime.utcnow()
        })
        
        return {
            "subscription_id": stripe_subscription.id,
            "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/channel/{channel_id}")
async def get_channel_subscribers(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    # Get channel
    channel = await db.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    # Verify ownership
    if channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this channel's subscribers"
        )
    
    return await db.get_channel_subscribers(channel_id)

@router.post("/webhook")
async def subscription_webhook(payload: dict):
    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
        
        if event.type == "customer.subscription.updated":
            subscription = event.data.object
            await db.update_subscription(subscription.id, {
                "status": subscription.status
            })
            
        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object
            await db.update_subscription(subscription.id, {
                "status": "canceled"
            })
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
