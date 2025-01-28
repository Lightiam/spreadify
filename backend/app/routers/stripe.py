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

@router.post("/webhook")
async def stripe_webhook(request: Request):
    try:
        event = stripe.Webhook.construct_event(
            payload=await request.body(),
            sig_header=request.headers.get("stripe-signature"),
            secret=os.getenv("STRIPE_WEBHOOK_SECRET")
        )
        
        if event.type == "checkout.session.completed":
            session = event.data.object
            # Handle successful payment
            print(f"Payment successful for session: {session.id}")
            
            # Extract subscription details from metadata
            user_id = session.metadata.get('user_id')
            plan_type = session.metadata.get('plan_type', 'monthly')
            subscription_id = session.subscription
            
            if not user_id:
                raise HTTPException(status_code=400, detail="User ID not found in session metadata")
                
            # TODO: Update user subscription status in database
            # subscription_data = {
            #     'status': 'active',
            #     'plan': session.metadata.get('price_id'),
            #     'subscription_id': subscription_id,
            #     'billing_cycle': plan_type,
            #     'current_period_end': None  # Will be set when we get subscription details
            # }
            
        elif event.type == "customer.subscription.updated":
            subscription = event.data.object
            # TODO: Update subscription status in database
            # subscription_data = {
            #     'current_period_end': subscription.current_period_end,
            #     'status': subscription.status
            # }
            
        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object
            # TODO: Update subscription status to cancelled in database
            # subscription_data = {
            #     'status': 'cancelled',
            #     'cancelled_at': subscription.canceled_at
            # }
            
        return JSONResponse(content={"status": "success"})
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
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
