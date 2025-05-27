import Loading from '@/pages/Loading';
import { createContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useCookies } from 'react-cookie';

interface SessionContextType {
    // isAuthenticated: boolean;
    isLoading: boolean;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

const SetupOrderStateAPI = async () => {
    try {
        const base: string = import.meta.env.VITE_BACKEND_API_URL;
        const response = await fetch(base + '/auth/setorder', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        console.log(data);
        if (!data.status_code || data.status_code !== 200) {
            throw new Error('Failed to set up order state');
        }
        return 
    } catch (error) {
        console.error('Setup Order_state failed:', error);
    } 
}

export const SessionProvider: React.FC<{ children: ReactNode; }> = ({ children }) => {
    // const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [cookies] = useCookies(['order_state']);

    useEffect(() => {
        const fetchOrderState = async () => {
            setIsLoading(true);
            const order_state = await SetupOrderStateAPI();
            cookies.order_state = order_state;
            setIsLoading(false);
        };
        fetchOrderState();
    }, [cookies.order_state]);

    return (
        isLoading ?
        <SessionContext.Provider value={{ isLoading }}>
            {children}
        </SessionContext.Provider>
        : <Loading />
    );
};


// export const useSession = (): SessionContextType => {
//     const context = useContext(SessionContext);
//     if (context === undefined) {
//         throw new Error('useSession must be used within a SessionProvider');
//     }
//     return context;
// };
