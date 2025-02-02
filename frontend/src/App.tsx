import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth';
import { useEffect } from 'react';
import Home from '@/pages/Home';
import { LoginForm } from '@/components/auth/LoginForm';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { AuthCallback } from '@/components/auth/AuthCallback';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import Dashboard from '@/pages/Dashboard';
import Stream from '@/pages/Stream';
import Channel from '@/pages/Channel';

const queryClient = new QueryClient();

function App() {
  const { setToken } = useAuth();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setToken(token);
    }
  }, [setToken]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/streams/:id"
            element={
              <ProtectedRoute>
                <Stream />
              </ProtectedRoute>
            }
          />
          <Route
            path="/channels/:id"
            element={
              <ProtectedRoute>
                <Channel />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
      {/* Sonner handles toast notifications automatically */}
    </QueryClientProvider>
  )
}

export default App
