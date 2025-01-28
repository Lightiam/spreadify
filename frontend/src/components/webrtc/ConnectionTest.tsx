import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api-client';

export function ConnectionTest() {
  const [status, setStatus] = useState<string>('Disconnected');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Create a test room ID
    const roomId = 'test-room-' + Date.now();
    
    try {
      const ws = apiClient.createSignalingChannel(roomId);
      
      // Add error handling for authentication failures
      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection failed - please ensure you are logged in');
        setStatus('Error');
      };
      
      // Send a test message when connection is established
      ws.onopen = () => {
        setStatus('Connected');
        const testMessage = {
          type: 'test',
          from: 'test-client',
          payload: { message: 'Test connection' }
        };
        ws.send(JSON.stringify(testMessage));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);
        setStatus(`Received message: ${JSON.stringify(data)}`);
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket error occurred');
        setStatus('Error');
      };

      ws.onclose = () => {
        setStatus('Disconnected');
      };

      // Cleanup on unmount
      return () => {
        ws.close();
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('Error');
    }
  }, []);

  return (
    <div className="p-4 border rounded-lg">
      <h2 className="text-lg font-semibold mb-2">WebRTC Connection Test</h2>
      <div className="space-y-2">
        <p>Status: <span className={`font-medium ${status === 'Connected' ? 'text-green-600' : 'text-red-600'}`}>{status}</span></p>
        {error && <p className="text-red-600">Error: {error}</p>}
      </div>
    </div>
  );
}
