import { API_BASE_URL } from './constants'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.error?.message || `API request failed (${response.status})`
    const error = new Error(message)
    error.code = payload?.error?.code
    error.status = response.status
    error.details = payload?.error?.details
    throw error
  }
  return payload?.data
}

export const fetchCurrentUser = () => request('/auth/me')
export const login = (email, password) =>
  request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
export const register = (name, email, password) =>
  request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  })
export const logout = () => request('/auth/logout', { method: 'POST' })

export const fetchCustomers = () => request('/customers')
export const fetchProducts = () => request('/products')
export const fetchSubscriptions = () => request('/subscriptions')
export const fetchCustomerDashboard = (customerId) =>
  request(`/customers/${customerId}/dashboard`)
export const fetchCustomerTimeline = (customerId) =>
  request(`/customers/${customerId}/timeline`)

export const generateBrief = (context) =>
  request('/generate-brief', {
    method: 'POST',
    body: JSON.stringify(context),
  })

export const refreshIntelligence = (customerId, period = {}) =>
  request(`/customers/${customerId}/intelligence/refresh`, {
    method: 'POST',
    body: JSON.stringify(period),
  })

export const deleteCustomer = (customerId) =>
  request(`/customers/${customerId}`, { method: 'DELETE' })

export const deleteSubscription = (subscriptionId) =>
  request(`/subscriptions/${subscriptionId}`, { method: 'DELETE' })

export const createCustomer = (customer) =>
  request('/customers', {
    method: 'POST',
    body: JSON.stringify(customer),
  })

export const createProduct = (product) =>
  request('/products', {
    method: 'POST',
    body: JSON.stringify(product),
  })

export const createSubscription = (subscription) =>
  request('/subscriptions', {
    method: 'POST',
    body: JSON.stringify(subscription),
  })
