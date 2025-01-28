from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import stripe
import os
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Initialize Stripe with secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_IDS = {
    "standard": "price_standard",  # Replace with actual Stripe price IDs
    "professional": "price_professional",
    "business": "price_business"
}

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    current_user = Depends(get_current_user)
):
    try:
        data = await request.json()
        price_id = data.get('priceId')
        plan_type = data.get('planType', 'monthly')

        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID is required")

        if price_id == 'free':
            # Handle free tier subscription
            # TODO: Update user's subscription status to free tier
            return JSONResponse(content={"status": "success", "tier": "free"})

        stripe_price_id = PRICE_IDS.get(price_id)
        if not stripe_price_id:
            raise HTTPException(status_code=400, detail="Invalid price ID")

        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=["card"],
            line_items=[{
                "price": stripe_price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{os.getenv('FRONTEND_URL')}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/pricing",
            metadata={
                'user_id': str(current_user.id),
                'plan_type': plan_type
            }
        )
        return JSONResponse(content={"sessionId": checkout_session.id})
    except stripe.error.InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoint removed as per request - using direct session verification instead

@router.post("/verify-subscription")
async def verify_subscription(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """
    Verify subscription status directly after payment completion
    without relying on webhooks
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status != "paid":
            return JSONResponse(content={
                "status": "pending",
                "message": "Payment not yet completed"
            })
            
        if session.customer_email != current_user.email:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get subscription details directly
        if session.subscription:
            subscription = stripe.Subscription.retrieve(session.subscription)
            return JSONResponse(content={
                "status": "success",
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "current_period_end": subscription.current_period_end,
                    "plan": subscription.plan.id
                }
            })
        
        return JSONResponse(content={
            "status": "success",
            "session": session.id
        })
        
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-session")
async def verify_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status != "paid":
            raise HTTPException(status_code=400, detail="Payment not completed")
            
        if session.customer_email != current_user.email:
            raise HTTPException(status_code=403, detail="Unauthorized")
            
        # TODO: Update user subscription status in database
        return JSONResponse(content={"status": "success"})
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
