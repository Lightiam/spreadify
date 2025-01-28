import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Camera, Users, Settings, LogOut, CreditCard } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Login } from '@/pages/Login'
import { WebSocketTest } from '@/components/webrtc/WebSocketTest'
import { ConnectionTest } from '@/components/webrtc/ConnectionTest'

// Logout button component to properly use hooks
function LogoutButton() {
  const auth = useAuth();
  return (
    <Button 
      variant="ghost" 
      size="sm"
      onClick={auth.logout}
    >
      <LogOut className="mr-2 h-4 w-4" />
      Sign Out
    </Button>
  );
}

import { AuthContext, useAuth } from '@/lib/hooks/use-auth';

// Auth provider component
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const publicPaths = ['/', '/login', '/pricing', '/success'];
    const isPublicPath = publicPaths.includes(window.location.pathname);
    
    const fetchUser = async () => {
      try {
        const data = await apiClient.getCurrentUser();
        setUser(data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };
    
    // Skip auth check for public paths
    if (isPublicPath) {
      setLoading(false);
    } else {
      fetchUser();
    }
  }, []);
  
  const logout = async () => {
    // Clear any stored tokens/cookies
    document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    localStorage.removeItem('token');
    setUser(null);
    window.location.href = '/login';
  };

  const value = { user, loading, error, logout };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Protected route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
}

// Import the Studio page component
import { Studio } from '@/pages/Studio';
import { PricingPage } from '@/pages/Pricing';
import { SuccessPage } from '@/pages/Success';
import { LandingPage } from '@/pages/Landing';

function AppContent() {
  const { user, loading: authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  const publicPaths = ['/', '/login', '/pricing', '/success'];
  const isPublicPath = publicPaths.includes(window.location.pathname);

  // Skip auth loading state for public paths
  if (authLoading && !isPublicPath) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  // Only redirect from login if we have a user
  if (user && window.location.pathname === '/login') {
    return <Navigate to="/studio" replace />;
  }

  // Require auth for non-public paths
  if (!user && !isPublicPath) {
    return <Navigate to="/login" replace />;
  }

  // Only show navigation when user is logged in and not on public pages
  const showNavigation = user && !isPublicPath;

  return (
    <div className="min-h-screen bg-gray-100">
      {showNavigation && (
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex items-center">
                  <Link to="/" className="text-xl font-bold text-indigo-600">
                    Spreadify AI
                  </Link>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/studio">
                    <Camera className="mr-2 h-4 w-4" />
                    Studio
                  </Link>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/guests">
                    <Users className="mr-2 h-4 w-4" />
                    Guests
                  </Link>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/settings">
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </Link>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/test">
                    <Camera className="mr-2 h-4 w-4" />
                    Test WebRTC
                  </Link>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/pricing">
                    <CreditCard className="mr-2 h-4 w-4" />
                    Pricing
                  </Link>
                </Button>
                <LogoutButton />
              </div>
            </div>
          </div>
        </nav>
      )}
      <main className={user ? "max-w-7xl mx-auto py-6 sm:px-6 lg:px-8" : ""}>
        <Routes>
          <Route 
            path="/studio" 
            element={
              <ProtectedRoute>
                <Studio />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/guests" 
            element={
              <ProtectedRoute>
                <div>Guests Page (Coming Soon)</div>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute>
                <div>Settings Page (Coming Soon)</div>
              </ProtectedRoute>
            } 
          />
          <Route path="/login" element={<Login />} />
          <Route 
            path="/websocket-test" 
            element={
              <ProtectedRoute>
                <WebSocketTest />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/test" 
            element={
              <ProtectedRoute>
                <ConnectionTest />
              </ProtectedRoute>
            } 
          />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/success" element={<SuccessPage />} />
          <Route path="/" element={<LandingPage />} />
          <Route path="*" element={<Navigate to="/studio" replace />} />
        </Routes>
      </main>
    </div>
  );
}

import { Toaster } from "@/components/ui/toaster";

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
        <Toaster />
      </AuthProvider>
    </Router>
  );
}

export default App
