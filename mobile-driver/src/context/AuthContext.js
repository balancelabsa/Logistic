import React, { createContext, useContext, useState } from 'react';
import api from '../api/client';
import { stopBackgroundTracking } from '../services/locationService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);

  const login = async (phone, password) => {
    const { data } = await api.post('/auth/login', { phone, password });
    setToken(data.access_token);
    api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
    return data;
  };

  const logout = async () => {
    await stopBackgroundTracking();
    setToken(null);
    delete api.defaults.headers.common.Authorization;
  };

  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
