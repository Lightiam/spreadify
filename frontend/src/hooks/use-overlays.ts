import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Overlay {
  id: string;
  stream_id: string;
  path: string;
  position_x: number;
  position_y: number;
  scale: number;
  active: boolean;
}

export function useOverlays(streamId: string) {
  const [overlays, setOverlays] = useState<Overlay[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOverlays = async () => {
      try {
        const response = await api.get(`/overlays/${streamId}`);
        setOverlays(response.data);
        setError(null);
      } catch (err) {
        setError("Failed to load overlays");
        console.error("Error loading overlays:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOverlays();
    const interval = setInterval(fetchOverlays, 5000);

    return () => clearInterval(interval);
  }, [streamId]);

  return { overlays, isLoading, error };
}
