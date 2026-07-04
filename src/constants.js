// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api'

// Brief Generation Mock Data
export const MOCK_CUSTOMERS = [
  { id: 'abc-bank', name: 'ABC Bank' },
  { id: 'green-tech', name: 'Green Tech' },
  { id: 'neo-retail', name: 'Neo Retail' },
]

export const MEETING_TYPES = ['QBR', 'Renewal', 'Discovery', 'Upsell']
export const PRODUCTS = ['CRM Platform', 'Collaboration Tool', 'Business Analytics Software']
export const DELIVERABLES = ['Call', 'Email', 'Meeting Agenda', 'Executive Report']

// Brief Generation Delay (milliseconds) - simulates API latency
export const BRIEF_GENERATION_DELAY = 600

// UI Constants
export const MAX_NOTES_LENGTH = 500
export const DATE_FORMAT = 'en-US'
