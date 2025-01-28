import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api-client';

export function SuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    const verifyPayment = async () => {
      if (!sessionId) {
        setStatus('error');
        return;
      }

      try {
        // Check if we're in test mode (mock session ID)
        if (sessionId.startsWith('mock_session_')) {
          console.log('Test mode - Simulating successful payment');
          setStatus('success');
          return;
        }

        // Real payment verification
        const result = await apiClient.post<{ status: string; subscription?: { id: string; status: string; current_period_end: number; plan: string; } }>('/api/stripe/verify-subscription', { sessionId });
        if (result.status === 'success') {
          setStatus('success');
        } else if (result.status === 'pending') {
          // Retry after 5 seconds if payment is still pending
          setTimeout(() => verifyPayment(), 5000);
        } else {
          throw new Error('Payment verification failed');
        }
      } catch (error) {
        console.error('Payment verification failed:', error);
        setStatus('error');
      }
    };

    verifyPayment();
  }, [sessionId]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
        {status === 'loading' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <h2 className="mt-4 text-xl font-semibold">Verifying your payment...</h2>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="mt-4 text-2xl font-bold">Payment Successful!</h2>
            <p className="mt-2 text-gray-600">
              Thank you for upgrading your Spreadify AI account. Your new features are now available.
            </p>
            <div className="mt-6">
              <Button
                onClick={() => navigate('/studio')}
                className="w-full"
              >
                Go to Studio
              </Button>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="mt-4 text-2xl font-bold">Payment Verification Failed</h2>
            <p className="mt-2 text-gray-600">
              We couldn't verify your payment. Please contact support if you believe this is an error.
            </p>
            <div className="mt-6 space-y-2">
              <Button
                onClick={() => navigate('/pricing')}
                variant="outline"
                className="w-full"
              >
                Return to Pricing
              </Button>
              <Button
                onClick={() => window.location.href = 'mailto:support@spreadify.ai'}
                className="w-full"
              >
                Contact Support
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
