/**
 * Authentication hook for managing user state and authentication flow.
 */
import {
  useState,
  useEffect,
  useContext,
  createContext,
  ReactNode,
} from 'react';
import { useRouter } from 'next/router';
import { authApi } from '@/lib/api';
import { IUser, IAuthContext } from '@/types/playlist';

const AuthContext = createContext<IAuthContext | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<IUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check for existing token and validate user
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token is invalid, remove it
          localStorage.removeItem('access_token');
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Handle OAuth callback
  useEffect(() => {
    if (!router.isReady) return;

    const handleCallback = async () => {
      const { code, state } = router.query;

      if (code && typeof code === 'string') {
        try {
          setIsLoading(true);
          const tokenResponse = await authApi.callback(
            code,
            typeof state === 'string' ? state : undefined,
          );

          // Store token
          localStorage.setItem('access_token', tokenResponse.access_token);

          // Get user data
          const userData = await authApi.getCurrentUser();
          setUser(userData);

          // Redirect to dashboard
          router.replace('/');
        } catch (error) {
          console.error('Authentication error:', error);
          router.replace('/?error=auth_failed');
        } finally {
          setIsLoading(false);
        }
      }
    };

    if (router.pathname === '/callback') {
      handleCallback();
    }
  }, [router.isReady, router.pathname, router.query]);

  const login = async (token: string) => {
    localStorage.setItem('access_token', token);
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      localStorage.removeItem('access_token');
      throw error;
    }
  };

  const logout = async () => {
    localStorage.removeItem('access_token');
    setUser(null);
    router.push('/');
  };

  const value: IAuthContext = {
    user,
    login,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): IAuthContext {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
