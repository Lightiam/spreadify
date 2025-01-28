import { useState, useCallback, useEffect } from 'react';
import { apiClient, ApiError } from '../api-client';

interface UseApiState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
}

interface UseApiResponse<T> extends UseApiState<T> {
  execute: (...args: any[]) => Promise<void>;
  reset: () => void;
}

export function useApi<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  immediate = false
): UseApiResponse<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    error: null,
    loading: false,
  });

  const execute = useCallback(
    async (...args: any[]) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const data = await apiFunction(...args);
        setState({ data, loading: false, error: null });
      } catch (error) {
        setState({
          data: null,
          loading: false,
          error: error as ApiError,
        });
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, error: null, loading: false });
  }, []);

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return {
    ...state,
    execute,
    reset,
  };
}

// Convenience hooks for common API operations
export function useCurrentUser(immediate = true) {
  const api = useApi(() => apiClient.getCurrentUser(), immediate);
  
  // Add token handling
  const handleOAuthCallback = useCallback(async (code: string) => {
    try {
      await apiClient.handleOAuthCallback(code);
      // Refresh user data after token is stored
      await api.execute();
    } catch (error) {
      console.error('Failed to handle OAuth callback:', error);
    }
  }, [api]);

  return { ...api, handleOAuthCallback };
}

export function useCreateStream() {
  return useApi(apiClient.createStream.bind(apiClient));
}

export function useListStreams(immediate = true) {
  return useApi(() => apiClient.listStreams(), immediate);
}

export function useStream(streamId: string, immediate = true) {
  return useApi(() => apiClient.getStream(streamId), immediate);
}
