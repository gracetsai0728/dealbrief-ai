import { useState } from 'react'
import { MeetingForm, ResultPanel, EngagementLog } from './components'
import './App.css'

const customers = [
  { id: 'abc-bank', name: 'ABC Bank' },
  { id: 'green-tech', name: 'Green Tech' },
  { id: 'neo-retail', name: 'Neo Retail' },
]

const meetingTypes = ['QBR', 'Renewal', 'Discovery', 'Upsell']
const products = ['CRM Platform', 'Collaboration Tool', 'Business Analytics Software']
const deliverables = ['Call', 'Email', 'Meeting Agenda', 'Executive Report']

function App() {
  const [customer, setCustomer] = useState(customers[0].id)
  const [meetingType, setMeetingType] = useState(meetingTypes[0])
  const [product, setProduct] = useState(products[0])
  const [deliverable, setDeliverable] = useState(deliverables[0])
  const [notes, setNotes] = useState('')
  const [result, setResult] = useState(null)
  const [log, setLog] = useState([])
  const [loading, setLoading] = useState(false)

  const generateMockBrief = () => {
    return {
      customerName: customers.find((c) => c.id === customer).name,
      meetingType,
      product,
      deliverable,
      overview:
        'ABC Bank CRM usage increased by 35% in the past 90 days, with license utilization at 82%. This indicates potential expansion needs.',
      talkingPoints: [
        'Observed significant CRM adoption growth and expansion indicators.',
        'Discussed workflow automation and reporting requirements.',
        'Evaluated additional licensing and feature expansion opportunities.',
      ],
      questions: [
        'Is this usage growth driven by new business units or teams?',
        'What are the primary reporting and analytics pain points?',
        'Are there planned team expansions or new module deployments?',
      ],
      nextSteps:
        'Schedule a follow-up meeting to discuss license planning, workflow automation, and potential expansion options.',
      risk: 'Low feature adoption may impact renewal negotiations.',
      notes,
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setResult(null)

    // Replace with fetch('/api/generate-brief') when backend is ready
    await new Promise((resolve) => setTimeout(resolve, 600))

    const brief = generateMockBrief()
    setResult(brief)
    setLog((prev) => [
      {
        id: Date.now(),
        createdAt: new Date().toLocaleString(),
        ...brief,
      },
      ...prev,
    ])
    setLoading(false)
  }

  return (
    <div className="app">
      <header className="hero-section">
        <div>
          <h1>DealBrief AI</h1>
          <p>Generate customer meeting briefs in seconds. Prepare smarter, sell faster.</p>
        </div>
      </header>

      <MeetingForm
        customer={customer}
        setCustomer={setCustomer}
        meetingType={meetingType}
        setMeetingType={setMeetingType}
        product={product}
        setProduct={setProduct}
        deliverable={deliverable}
        setDeliverable={setDeliverable}
        notes={notes}
        setNotes={setNotes}
        customers={customers}
        meetingTypes={meetingTypes}
        products={products}
        deliverables={deliverables}
        onGenerate={handleGenerate}
        loading={loading}
      />

      <ResultPanel result={result} />

      <EngagementLog log={log} />
    </div>
  )
}

export default App
