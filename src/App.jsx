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
const deliverables = ['Call', 'Email', 'Meeting Agenda']

function App() {
  const [customer, setCustomer] = useState(customers[0].id)
  const [meetingType, setMeetingType] = useState(meetingTypes[0])
  const [product, setProduct] = useState(products[0])
  const [deliverable, setDeliverable] = useState(deliverables[0])
  const [notes, setNotes] = useState('')
  const [result, setResult] = useState(null)
  const [log, setLog] = useState([])
  const [selectedLogItem, setSelectedLogItem] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('new')
  const [selectedCustomerForLog, setSelectedCustomerForLog] = useState(null)

  const getCustomersWithLogs = () => {
    const uniqueCustomers = new Set(log.map((item) => item.customerName))
    return Array.from(uniqueCustomers)
  }

  const getLogsForCustomer = (customerName) => {
    return log.filter((item) => item.customerName === customerName)
  }

  const generateMockBrief = () => {
    const customerName = customers.find((c) => c.id === customer).name
    const common = {
      customerName,
      meetingType,
      product,
      deliverable,
      overview:
        `${customerName}'s ${product} usage increased by 35% in the past 90 days, with utilization at 82%. This indicates potential expansion needs.`,
      notes,
    }

    if (deliverable === 'Email') {
      return {
        ...common,
        email: {
          to: `${customerName} team`,
          subject: `${meetingType} follow-up: ${product} opportunities and next steps`,
          greeting: `Hi ${customerName} team,`,
          paragraphs: [
            `Thank you for the conversation about your ${product}. We saw strong momentum, including 35% usage growth over the past 90 days.`,
            'Based on our discussion, workflow automation, reporting, and future capacity planning are the highest-impact areas to explore next.',
          ],
          callToAction: 'Would you be available for a 30-minute follow-up next week to review recommendations and agree on an action plan?',
          signOff: 'Best,\nYour Account Team',
        },
      }
    }

    if (deliverable === 'Meeting Agenda') {
      return {
        ...common,
        objective: `Align on ${customerName}'s priorities for ${product} and agree on concrete next steps.`,
        duration: '45 minutes',
        agendaItems: [
          { time: '5 min', title: 'Welcome and desired outcomes', detail: 'Confirm goals and priorities for the session.' },
          { time: '10 min', title: 'Current-state review', detail: 'Review adoption, usage growth, and key business context.' },
          { time: '15 min', title: 'Priorities and challenges', detail: 'Discuss workflow automation, reporting needs, and expansion plans.' },
          { time: '10 min', title: 'Recommendations', detail: `Review opportunities to increase value from ${product}.` },
          { time: '5 min', title: 'Decisions and next steps', detail: 'Assign owners, deadlines, and the follow-up date.' },
        ],
        preparation: [
          'Review the latest usage and adoption metrics.',
          'Bring examples of current workflow or reporting challenges.',
          'Identify stakeholders needed for follow-up decisions.',
        ],
        desiredOutcome: 'A prioritized action plan with clear owners and a scheduled follow-up.',
      }
    }

    return {
      ...common,
      callObjective: `Understand ${customerName}'s priorities and identify the strongest expansion opportunity for ${product}.`,
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
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setResult(null)

    // Replace with fetch('/api/generate-brief') when backend is ready
    await new Promise((resolve) => setTimeout(resolve, 600))

    const brief = generateMockBrief()
    setResult(brief)
    setLoading(false)
    setActiveTab('brief')
  }

  const handleLogEngagement = () => {
    if (result) {
      const loggedCustomerName = result.customerName

      setLog((prev) => [
        {
          id: Date.now(),
          createdAt: new Date().toLocaleString(),
          ...result,
        },
        ...prev,
      ])
      setResult(null)
      setSelectedCustomerForLog(loggedCustomerName)
      setActiveTab('previous')
    }
  }

  return (
    <div className="app">
      <header className="hero-section">
        <div>
          <h1>DealBrief AI</h1>
          <p>Generate customer meeting briefs in seconds. Prepare smarter, sell faster.</p>
        </div>
      </header>

      <div className="tabs-container">
        <div className="tabs-nav">
          <button
            className={`tab-button ${activeTab === 'new' ? 'active' : ''}`}
            onClick={() => setActiveTab('new')}
          >
            New Meeting
          </button>
          <button
            className={`tab-button ${activeTab === 'brief' ? 'active' : ''}`}
            onClick={() => setActiveTab('brief')}
          >
            Generated Brief
          </button>
          <button
            className={`tab-button ${activeTab === 'previous' ? 'active' : ''}`}
            onClick={() => setActiveTab('previous')}
          >
            Previous Engagement
          </button>
        </div>

        <div className="tabs-content">
          {activeTab === 'new' && (
            <div className="new-meeting-tab">
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
            </div>
          )}

          {activeTab === 'brief' && (
            <div className="brief-tab">
              {result ? (
                <>
                  <ResultPanel result={result} onLogEngagement={handleLogEngagement} />
                </>
              ) : (
                <p className="no-data">Generate a brief from the New Meeting tab to see it here.</p>
              )}
            </div>
          )}

          {activeTab === 'previous' && (
            <div className="previous-engagement-tab">
              {getCustomersWithLogs().length === 0 ? (
                <p className="no-data">No engagement history yet</p>
              ) : (
                <div className="customer-tabs">
                  <div className="customer-tabs-nav" role="tablist" aria-label="Customer engagement history">
                    {getCustomersWithLogs().map((customerName) => (
                      <button
                        key={customerName}
                        type="button"
                        role="tab"
                        aria-selected={selectedCustomerForLog === customerName}
                        className={`customer-tab-button ${selectedCustomerForLog === customerName ? 'active' : ''}`}
                        onClick={() => {
                          setSelectedCustomerForLog(customerName)
                          setSelectedLogItem(null)
                        }}
                      >
                        {customerName}
                      </button>
                    ))}
                  </div>

                  {selectedCustomerForLog && (
                    <div className="customer-tab-content" role="tabpanel">
                      <div className="engagement-detail">
                  <div className="engagement-list">
                    <h3>{selectedCustomerForLog}</h3>
                    <EngagementLog
                      log={getLogsForCustomer(selectedCustomerForLog)}
                      onSelectItem={setSelectedLogItem}
                      selectedItemId={selectedLogItem?.id}
                    />
                  </div>

                  {selectedLogItem && selectedLogItem.customerName === selectedCustomerForLog && (
                    <ResultPanel
                      result={selectedLogItem}
                      isLogView
                      onClose={() => setSelectedLogItem(null)}
                    />
                  )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
