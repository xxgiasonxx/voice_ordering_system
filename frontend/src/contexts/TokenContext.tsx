// src/context/TokenContext.tsx
import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import axios from 'axios';

interface TokenContextType {
    // token: string | null;
    isLoading: boolean;
    refreshToken: () => Promise<void>;
}

const TokenContext = createContext<TokenContextType | undefined>(undefined);

export const TokenProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    // const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 呼叫後端 API 獲取 token (後端會自動設置 HttpOnly cookie)
    const fetchToken = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            
            await axios.get('http://localhost:8000/get-token', {
                withCredentials: true, // 確保 cookie 被包含在請求中
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to fetch token';
            setError(errorMessage);
            console.error('Failed to fetch token:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // 頁面載入時自動獲取 token (後端會設置 HttpOnly cookie)
    useEffect(() => {
        fetchToken();
    }, [fetchToken]);

    return (
        error ? (
            <div>Error: {error}</div>
        ):
        <TokenContext.Provider value={{ 
            // token, 
            isLoading, 
            refreshToken: fetchToken 
        }}>
            {children}
        </TokenContext.Provider>
    );
};

// 自訂 Hook 用於存取 token
export const useToken = () => {
    const context = useContext(TokenContext);
    if (!context) {
        throw new Error('useToken must be used within a TokenProvider');
    }
    return context;
};