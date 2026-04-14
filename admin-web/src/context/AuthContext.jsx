import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('admin_token'))
  const [user, setUser] = useState(null)

  const login = async (phone, password) => {
    const { data } = await api.post('/auth/login', { phone, password })
    localStorage.setItem('admin_token', data.access_token)
    setToken(data.access_token)
    const me = await api.get('/auth/me', { headers: { Authorization: `Bearer ${data.access_token}` } })
    setUser(me.data)
  }

  const logout = () => {
    localStorage.removeItem('admin_token')
    setToken(null)
    setUser(null)
  }

  useEffect(() => {
    if (!token) return
    api.get('/auth/me').then((res) => setUser(res.data)).catch(() => logout())
  }, [token])

  const value = useMemo(() => ({ token, user, login, logout }), [token, user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
