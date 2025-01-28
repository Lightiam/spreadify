import { createContext, useContext } from 'react';

interface AuthContextType {
  user: any;
  loading: boolean;
  error: Error | null;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
