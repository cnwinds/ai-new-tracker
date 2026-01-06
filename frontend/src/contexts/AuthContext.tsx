/**
 * 认证上下文
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { message } from 'antd';
import { apiService } from '@/services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'auth_token';
const USERNAME_KEY = 'auth_username';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // 初始化时检查token
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const savedUsername = localStorage.getItem(USERNAME_KEY);
    
    if (token && savedUsername) {
      // 先设置token到API服务
      apiService.setToken(token);
      // 验证token是否有效
      verifyToken(token)
        .then((valid) => {
          if (valid) {
            setIsAuthenticated(true);
            setUsername(savedUsername);
          } else {
            // token无效，清除
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USERNAME_KEY);
            apiService.setToken(null);
          }
        })
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USERNAME_KEY);
          apiService.setToken(null);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (token: string): Promise<boolean> => {
    try {
      // 设置token到API服务
      apiService.setToken(token);
      // 验证token
      await apiService.verifyToken();
      return true;
    } catch (error) {
      return false;
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await apiService.login(username, password);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      localStorage.setItem(USERNAME_KEY, username);
      apiService.setToken(response.access_token);
      setIsAuthenticated(true);
      setUsername(username);
      message.success('登录成功');
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : '登录失败，请检查用户名和密码';
      message.error(errorMessage);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USERNAME_KEY);
    apiService.setToken(null);
    setIsAuthenticated(false);
    setUsername(null);
    message.success('已登出');
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
