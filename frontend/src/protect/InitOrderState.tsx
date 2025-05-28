// AuthGuard.tsx
import { useEffect, useState } from 'react';
import axios from 'axios';
import Loading from '@/pages/Loading';

const SetupOrderStateAPI = async () => {
    try {
        const base: string = import.meta.env.VITE_BACKEND_API_URL;
        const response = await axios.get(base + '/auth/setorder');

        console.log(response)

        if (response.status !== 200) {
            throw new Error('Failed to set up order state');
        }
        const data: string = response.statusText;
        if (!data || data !== 'OK') {
            throw new Error('Order state not found in response');
        }
        return true;
    } catch (error) {
        console.error('Setup Order_state failed:', error);
        return false;
    }
};

export const InitOrderState = ({ children }: { children: React.ReactNode }) => {
    const [loading, setLoading] = useState(true);


    useEffect(() => {
        const checkOrderState = async () => {
            setLoading(true);
            const state = await SetupOrderStateAPI();
            if (state === true){
                setLoading(false);
                return;
            }
        };

        checkOrderState();
    }, [setLoading]);

    return (
        loading ? <Loading /> :
            <>{children}</>
    )
};

export default InitOrderState;
