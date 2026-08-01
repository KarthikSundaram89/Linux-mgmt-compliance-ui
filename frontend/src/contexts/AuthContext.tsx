/**
 * Authentication context provider.
 * Manages auth state across the application.
 *
 * For GitHub Pages demo: auto-authenticates as admin user.
 */
import React, { createContext, useCallback, useEffect, useState } from 'react';
import { LoginCredentials, User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
});

// Demo user for GitHub Pages visualization
const DEMO_USER: User = {
  id: 'u-001',
  username: 'admin',
  email: 'admin@company.com',
  full_name: 'System Administrator',
  role: 'admin',
  last_login_at: new Date().toISOString(),
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  // Auto-authenticate for demo mode
  useEffect(() => {
    // In demo/mock mode, auto-login as admin
    setUser(DEMO_USER);
    localStorage.setItem('access_token', 'mock-token');
    setIsLoading(false);
  }, []);

  const login = useCallback(async (_credentials: LoginCredentials) => {
    // Mock login - always succeeds
    setUser(DEMO_USER);
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('refresh_token', 'mock-refresh');
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // In demo mode, re-login immediately
    setTimeout(() => {
      setUser(DEMO_USER);
      localStorage.setItem('access_token', 'mock-token');
    }, 100);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
