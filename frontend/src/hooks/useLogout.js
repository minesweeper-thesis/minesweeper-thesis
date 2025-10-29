import {useAuth} from '../contexts/AuthContext';
import {useNavigate} from 'react-router-dom';

export const useLogout = () => {
    const { setUser } = useAuth();
    const navigate = useNavigate();

    return async () => {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
        } catch (err) {
            console.error('Logout failed', err);
        } finally {
            setUser(null);
            navigate('/');
        }
    };
};
