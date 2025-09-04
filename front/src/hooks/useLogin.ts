import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAtom } from 'jotai';
import { authAtom } from '../contexts/AuthContext';
import { userService } from '../services/api/api';

export function useLogin() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, setAuth] = useAtom(authAtom);
  const navigate = useNavigate();

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await userService.login({ email, password });
      setAuth({ token: response.token, user: response.user });

      navigate('/Chat', { state: { user_id: response.user_id } });
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return { login, loading, error };
}
