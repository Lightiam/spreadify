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
    const code = searchParams.get('code');
    const error = searchParams.get('error');
    
    if (error) {
      setError(decodeURIComponent(error));
      // Remove error from URL
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
      return;
    }
    
    if (code) {
      setIsLoading(true);
      // The code is our JWT token from the backend
      console.log('Received OAuth code:', code);
      
      // Store token in both localStorage and cookies for different auth mechanisms
      localStorage.setItem('token', code);
      console.log('Stored token in localStorage:', localStorage.getItem('token'));
      
      // Set cookie with proper attributes for WebSocket access
      const secure = window.location.protocol === 'https:' ? 'secure;' : '';
      const cookieValue = `token=${code}; path=/; ${secure} samesite=lax; max-age=3600`;
      document.cookie = cookieValue;
      console.log('Setting cookie with value:', cookieValue);
      
      // Remove the code from the URL
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
      
      // Log cookie status for debugging
      console.log('All cookies after setting:', document.cookie);
      
      // Double check cookie was set
      const cookies = document.cookie.split(';');
      console.log('Parsed cookies:', cookies);
      const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('token='));
      console.log('Found token cookie:', tokenCookie);
      
      // Redirect to studio
      navigate('/studio');
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
            Sign in to Spreadify AI
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start streaming to multiple platforms
          </p>
        </div>
        {error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
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
