import { useEffect } from 'react';
import { WebSocketConnectionTest } from '@/components/webrtc/WebSocketConnectionTest';
import { useAuth } from '@/lib/hooks/use-auth';
import { useNavigate } from 'react-router-dom';

export function Studio() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    }
  }, [user, loading, navigate]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Spreadify AI Studio</h1>
      <div className="grid gap-4">
        <WebSocketConnectionTest />
      </div>
    </div>
  );
}
