import { createContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useCookies } from 'react-cookie';

interface SessionContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

const FetchSessionFromAPI = async ({setIsAuthenticated, setIsLoading}: {
    setIsAuthenticated: React.Dispatch<React.SetStateAction<boolean>>;
    setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
    try {
        const base: string = import.meta.env.VITE_BACKEND_API_URL;
        const response = await fetch(base + '/auth/validate', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        console.log(data);
        if (!data.valid){
            throw new Error('Session validation failed');
        }
        // cookies.ordering_system_session = data.ordering_system_session;
        setIsAuthenticated(true);
        setIsLoading(false);
    } catch (error) {
        console.error('Session validation failed:', error);
        setIsAuthenticated(false);
    } finally {
        setIsLoading(false);
    }
}

export const SessionProvider: React.FC<{ children: ReactNode; }> = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [cookies] = useCookies(['ordering_system_session']);

    useEffect(() => {
        const validateSession = async () => {
            if (isAuthenticated) {
                return;
            }
            
            setIsLoading(true);
            
            if (!cookies.ordering_system_session) {
                FetchSessionFromAPI({setIsAuthenticated, setIsLoading});
                return;
            }
            
            setIsAuthenticated(true);
            setIsLoading(false);
        };

        validateSession();
    }, [cookies.ordering_system_session, isAuthenticated, setIsAuthenticated, setIsLoading]);

    return (
        isAuthenticated ?
        <SessionContext.Provider value={{ isAuthenticated, isLoading }}>
            {children}
        </SessionContext.Provider>
        : (
            <div className="flex items-center justify-center h-screen">
                <h1 className="text-2xl font-bold">Session is not authenticated</h1>
            </div>
        )
    );
};

// export const useSession = (): SessionContextType => {
//     const context = useContext(SessionContext);
//     if (context === undefined) {
//         throw new Error('useSession must be used within a SessionProvider');
//     }
//     return context;
// };
