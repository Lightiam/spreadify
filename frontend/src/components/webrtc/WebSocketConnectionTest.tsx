import { useEffect, useState } from 'react';
import { env } from '@/lib/env';
import { Button } from '@/components/ui/button';

export function WebSocketConnectionTest() {
  console.log('WebSocket URL from env:', env.WEBSOCKET_URL); // Debug log
  const [status, setStatus] = useState<string>('Not connected');
  const [messages, setMessages] = useState<string[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Cleanup function
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  const connect = async () => {
    try {
      // Get test token from backend
      const response = await fetch('http://localhost:8000/auth/test-token');
      const token = await response.text();
      
      // Create WebSocket URL with token
      // Remove any quotes from the token string
      const cleanToken = token.replace(/^"|"$/g, '');
      if (!env.WEBSOCKET_URL) {
        throw new Error('WebSocket URL is not configured');
      }
      const wsUrl = `${env.WEBSOCKET_URL}/test-room?token=${encodeURIComponent(cleanToken)}`;
      console.log('WebSocket URL:', env.WEBSOCKET_URL);
      console.log('Clean token:', cleanToken);
      console.log('Connecting to WebSocket:', wsUrl);
      
      const newWs = new WebSocket(wsUrl);
      
      newWs.onopen = () => {
        console.log('WebSocket connected');
        setStatus('Connected');
        
        // Send test message
        newWs.send(JSON.stringify({
          type: 'test',
          from: 'browser-test',
          data: 'Hello from browser'
        }));
      };
      
      newWs.onmessage = (event) => {
        console.log('Received message:', event.data);
        setMessages(prev => [...prev, event.data]);
      };
      
      newWs.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('Error connecting');
      };
      
      newWs.onclose = () => {
        console.log('WebSocket closed');
        setStatus('Disconnected');
      };
      
      setWs(newWs);
    } catch (error) {
      console.error('Failed to connect:', error);
      setStatus('Error connecting');
    }
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      setWs(null);
    }
  };

  return (
    <div className="p-4 border rounded-lg">
      <h2 className="text-lg font-semibold mb-4">WebSocket Test</h2>
      <div className="space-y-4">
        <div>
          <strong>Status:</strong> {status}
        </div>
        <div className="space-x-2">
          <Button
            onClick={connect}
            disabled={!!ws}
          >
            Connect
          </Button>
          <Button
            onClick={disconnect}
            disabled={!ws}
            variant="destructive"
          >
            Disconnect
          </Button>
        </div>
        <div>
          <strong>Messages:</strong>
          <pre className="mt-2 p-2 bg-gray-100 rounded">
            {messages.map((msg, i) => (
              <div key={i}>{msg}</div>
            ))}
          </pre>
        </div>
      </div>
    </div>
  );
}
