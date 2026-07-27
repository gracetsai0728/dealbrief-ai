import { API_BASE_URL } from './constants'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
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

export const fetchCustomers = () => request('/customers')
export const fetchProducts = () => request('/products')
export const fetchUsage = () => request('/usage')
export const fetchEngagementLog = () => request('/engagement-log')
export const fetchImportJobs = () => request('/imports')
export const fetchCustomerDashboard = (customerId) =>
  request(`/customers/${customerId}/dashboard`)

export const generateBrief = (context) =>
  request('/generate-brief', {
    method: 'POST',
    body: JSON.stringify(context),
  })

export const saveBrief = (engagementId) =>
  request('/engagement-log', {
    method: 'POST',
    body: JSON.stringify({ engagementId }),
  })

export const importCustomers = (filename, rows) =>
  request('/imports/customers', {
    method: 'POST',
    body: JSON.stringify({ filename, rows }),
  })

export const importUsage = (filename, rows) =>
  request('/imports/usage', {
    method: 'POST',
    body: JSON.stringify({ filename, rows }),
  })

export const refreshIntelligence = (customerId, period = {}) =>
  request(`/customers/${customerId}/intelligence/refresh`, {
    method: 'POST',
    body: JSON.stringify(period),
  })

export const deleteCustomer = (customerId) =>
  request(`/customers/${customerId}`, { method: 'DELETE' })

export const deleteUsage = (usageId) =>
  request(`/usage/${usageId}`, { method: 'DELETE' })

export const deleteEngagement = (engagementId) =>
  request(`/engagement-log/${engagementId}`, { method: 'DELETE' })
