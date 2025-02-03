from fastapi import APIRouter
from . import paypal

router = APIRouter(prefix="/payments", tags=["payments"])

# Include the PayPal router
router.include_router(paypal.router)
