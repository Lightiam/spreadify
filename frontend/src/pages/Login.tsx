import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from "@/components/ui/button"
// Removed unused import
import { apiClient } from '@/lib/api-client';

export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check for auth callback
    const searchParams = new URLSearchParams(location.search);
    const token = searchParams.get('token');
    const error = searchParams.get('error');
    const errorMessage = searchParams.get('message');
    
    if (error) {
      const message = errorMessage ? decodeURIComponent(errorMessage) : 'Authentication failed';
      setError(message);
      // Remove error from URL
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
      setIsLoading(false);
      return;
    }
    
    if (token) {
      setIsLoading(true);
      try {
        // Store token in localStorage
        localStorage.setItem('token', token);
        
        // Set secure cookie for WebSocket
        const secure = window.location.protocol === 'https:' ? 'secure;' : '';
        const domain = window.location.hostname;
        const cookieValue = `token=${token}; path=/; ${secure} domain=${domain}; samesite=lax; max-age=3600`;
        document.cookie = cookieValue;
        
        // Clean URL
        const newUrl = window.location.pathname;
        window.history.replaceState({}, '', newUrl);
        
        // Redirect to studio
        navigate('/studio');
      } catch (error) {
        console.error('Error handling authentication token:', error);
        setError('Failed to process authentication token. Please try again.');
        setIsLoading(false);
      }
    }
  }, [location, navigate]);

  const handleGoogleLogin = async () => {
    try {
      setError(null);
      setIsLoading(true);
      // This will handle the redirect internally
      await apiClient.loginWithGoogle();
    } catch (error: any) {
      console.error('Failed to initiate Google login:', error);
      setError(error.message || 'Failed to initiate login. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Spreadify A
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start streaming to multiple platforms
          </p>
        </div>
        {error && (
          <div className="mt-2 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Authentication Error</h3>
                <p className="mt-1 text-sm text-red-600">{error}</p>
                <p className="mt-2 text-sm text-red-600">
                  Please ensure you have a verified email address and try again. If the problem persists, contact support.
                </p>
              </div>
            </div>
          </div>
        )}
        <div className="mt-8 space-y-6">
          <Button
            className="w-full flex justify-center py-2 px-4"
            onClick={handleGoogleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing in...
              </div>
            ) : (
              'Sign in with Google'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
