import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from '@/pages/Home';
import Dashboard from '@/pages/Dashboard';
import Stream from '@/pages/Stream';
import Channel from '@/pages/Channel';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/streams/:id" element={<Stream />} />
          <Route path="/channels/:id" element={<Channel />} />
        </Routes>
      </Router>
      {/* Sonner handles toast notifications automatically */}
    </QueryClientProvider>
  )
}

export default App
