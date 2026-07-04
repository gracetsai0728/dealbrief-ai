import { API_BASE_URL } from './constants'

/**
 * Generate a brief from the backend API
 * @param {Object} context - The meeting context
 * @param {string} context.customer - Customer ID
 * @param {string} context.meetingType - Meeting type
 * @param {string} context.product - Product
 * @param {string} context.deliverable - Deliverable format
 * @param {string} context.notes - Additional notes
 * @returns {Promise<Object>} The generated brief
 */
export async function generateBrief(context) {
  try {
    const response = await fetch(`${API_BASE_URL}/generate-brief`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(context),
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to generate brief:', error)
    throw error
  }
}

/**
 * Fetch available customers from the backend
 * @returns {Promise<Array>} Array of customers
 */
export async function fetchCustomers() {
  try {
    const response = await fetch(`${API_BASE_URL}/customers`)

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to fetch customers:', error)
    throw error
  }
}

/**
 * Save a brief to the engagement log
 * @param {Object} brief - The brief to save
 * @returns {Promise<Object>} The saved brief with ID
 */
export async function saveBrief(brief) {
  try {
    const response = await fetch(`${API_BASE_URL}/engagement-log`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(brief),
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to save brief:', error)
    throw error
  }
}

/**
 * Fetch engagement log history
 * @returns {Promise<Array>} Array of previous briefs
 */
export async function fetchEngagementLog() {
  try {
    const response = await fetch(`${API_BASE_URL}/engagement-log`)

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to fetch engagement log:', error)
    throw error
  }
}
