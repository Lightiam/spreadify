import { loadStripe } from '@stripe/stripe-js';
import { env } from '@/lib/env';

// Ensure the Stripe public key is available
if (!env.STRIPE_PUBLIC_KEY) {
  throw new Error('Missing Stripe public key');
}

// Create a singleton instance of the Stripe promise
export const stripePromise = loadStripe(env.STRIPE_PUBLIC_KEY);

// Types for Stripe checkout session
export interface CreateCheckoutSessionResponse {
  sessionId: string;
}

// Function to create a checkout session
export async function createCheckoutSession(priceId: string): Promise<string> {
  const response = await fetch('/api/stripe/create-checkout-session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ priceId }),
    credentials: 'include'
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create checkout session');
  }

  const { sessionId } = await response.json();
  return sessionId;
}

// Function to redirect to Stripe checkout
export async function redirectToCheckout(sessionId: string) {
  const stripe = await stripePromise;
  if (!stripe) {
    throw new Error('Stripe failed to initialize');
  }

  const { error } = await stripe.redirectToCheckout({ sessionId });
  if (error) {
    throw new Error(error.message);
  }
}

// Function to verify subscription status
export async function verifySubscription(sessionId: string): Promise<{
  status: string;
  subscription?: {
    id: string;
    status: string;
    current_period_end: number;
    plan: string;
  };
}> {
  const response = await fetch('/api/stripe/verify-subscription', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sessionId }),
    credentials: 'include'
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to verify subscription');
  }

  return response.json();
}
