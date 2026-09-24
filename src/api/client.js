import axios from 'axios'

const api = axios.create({ baseURL: '/market-watch' })

api.interceptors.response.use(
  res => res,
  err => {
    // A rejected login must stay on the form so its error can be shown.
    // Other expired sessions return to the app's configured base path.
    if (err.response?.status === 401 && !err.config?.url?.endsWith('/api/auth/login')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = `${import.meta.env.BASE_URL}login`
    }
    return Promise.reject(err)
  }
)

export default api
