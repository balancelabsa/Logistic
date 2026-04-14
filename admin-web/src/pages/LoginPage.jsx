import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const [phone, setPhone] = useState('900000001')
  const [password, setPassword] = useState('Admin@1234')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const onSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(phone, password)
      navigate('/')
    } catch {
      setError('فشل تسجيل الدخول، تحقق من البيانات')
    }
  }

  return (
    <div className="login-wrap">
      <form className="card" onSubmit={onSubmit}>
        <h2>دخول لوحة الإدارة</h2>
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="رقم الجوال" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="كلمة المرور" />
        {error && <p className="error">{error}</p>}
        <button type="submit">دخول</button>
      </form>
    </div>
  )
}
