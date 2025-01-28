import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

export const WebSocketTest = () => {
  const [status, setStatus] = useState<string>('Initializing...');
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const testWebSocket = async () => {
      try {
        // Create WebSocket connection
        const ws = apiClient.createSignalingChannel('test-room');
        setStatus('Connecting...');

        ws.onopen = () => {
          setStatus('Connected');
          // Send test message
          const message = {
            type: 'test',
            from: 'test-client',
            data: 'Hello, WebSocket server!'
          };
          ws.send(JSON.stringify(message));
          setMessages(prev => [...prev, 'Sent: ' + JSON.stringify(message)]);
        };

        ws.onmessage = (event) => {
          const response = JSON.parse(event.data);
          setMessages(prev => [...prev, 'Received: ' + JSON.stringify(response)]);
        };

        ws.onerror = (error) => {
          setStatus('Error: ' + (error instanceof Error ? error.message : String(error)));
        };

        ws.onclose = () => {
          setStatus('Disconnected');
        };

        // Cleanup
        return () => {
          ws.close();
        };
      } catch (error) {
        setStatus('Error: ' + (error instanceof Error ? error.message : String(error)));
      }
    };

    testWebSocket();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">WebSocket Test</h2>
      <div className="mb-4">
        <strong>Status:</strong> {status}
      </div>
      <div className="border rounded p-4">
        <h3 className="font-bold mb-2">Messages:</h3>
        {messages.map((msg, i) => (
          <div key={i} className="mb-1">
            {msg}
          </div>
        ))}
      </div>
    </div>
  );
};
