import { useMemo, useState } from 'react'
import './App.css'

const initialCustomers = [
  {
    id: 'abc-bank',
    name: 'ABC Bank',
    industry: 'Financial Services',
    accountOwner: 'Grace Lin',
    salesforceId: 'SF-ACCT-1042',
    opportunityStage: 'Renewal Review',
    renewalDate: '2026-10-15',
    status: 'Active',
    usageGrowth: '+35%',
    licenseUtilization: '82%',
    renewalRisk: 'Medium',
    lastInteraction: 'QBR follow-up on Jul 2',
    expansionSignal: 'Reporting add-on interest',
    nextBestAction: 'Prepare renewal value story',
    signal:
      'ABC Bank is showing strong CRM adoption, but renewal risk is elevated because advanced reporting usage is still uneven across teams.',
  },
  {
    id: 'northstar-retail',
    name: 'Northstar Retail',
    industry: 'Retail',
    accountOwner: 'Maya Chen',
    salesforceId: 'SF-ACCT-2088',
    opportunityStage: 'Expansion',
    renewalDate: '2026-12-01',
    status: 'Active',
    usageGrowth: '+48%',
    licenseUtilization: '91%',
    renewalRisk: 'Low',
    lastInteraction: 'Upsell discovery on Jun 28',
    expansionSignal: 'New store rollout',
    nextBestAction: 'Propose workflow expansion',
    signal:
      'Northstar Retail has rapid collaboration growth and high license utilization, making it a strong candidate for an upsell conversation.',
  },
  {
    id: 'greenhealth-group',
    name: 'GreenHealth Group',
    industry: 'Healthcare',
    accountOwner: 'Jordan Patel',
    salesforceId: 'SF-ACCT-3175',
    opportunityStage: 'Discovery',
    renewalDate: '2027-01-20',
    status: 'Pilot',
    usageGrowth: '+18%',
    licenseUtilization: '64%',
    renewalRisk: 'High',
    lastInteraction: 'Pilot check-in on Jul 1',
    expansionSignal: 'Executive dashboard request',
    nextBestAction: 'Align pilot success metrics',
    signal:
      'GreenHealth Group needs more proof of value before expansion. Usage is improving, but stakeholder alignment is still forming.',
  },
]

const initialUsageRecords = [
  {
    id: 'usage-abc-crm',
    customerId: 'abc-bank',
    product: 'CRM Platform',
    activeUsers: 410,
    licenseUtilization: '82%',
    usageGrowth: '+35%',
    featureAdoption: 'Reporting 58%, Automation 42%',
    lastUpdated: '2026-07-04',
  },
  {
    id: 'usage-northstar-collab',
    customerId: 'northstar-retail',
    product: 'Collaboration Tool',
    activeUsers: 780,
    licenseUtilization: '91%',
    usageGrowth: '+48%',
    featureAdoption: 'Channels 88%, Workflow approvals 63%',
    lastUpdated: '2026-07-05',
  },
  {
    id: 'usage-greenhealth-analytics',
    customerId: 'greenhealth-group',
    product: 'Business Analytics Software',
    activeUsers: 145,
    licenseUtilization: '64%',
    usageGrowth: '+18%',
    featureAdoption: 'Dashboards 51%, Forecasting 24%',
    lastUpdated: '2026-07-03',
  },
]

const baseTimelineEvents = [
  {
    id: 'event-1',
    customerId: 'abc-bank',
    date: '2026-07-04',
    eventType: 'Usage',
    source: 'Product Analytics',
    title: 'CRM license utilization reached 82%',
    summary: 'CRM active users increased across commercial banking and wealth management teams.',
    businessImpact: 'Expansion opportunity is increasing, especially for automation and reporting add-ons.',
    suggestedAction: 'Ask which teams are driving the growth and whether additional licenses are planned.',
  },
  {
    id: 'event-2',
    customerId: 'abc-bank',
    date: '2026-06-29',
    eventType: 'Meeting',
    source: 'Salesforce',
    title: 'Renewal opportunity moved to review stage',
    summary: 'The renewal opportunity was updated with procurement and security review as next steps.',
    businessImpact: 'Renewal timeline may tighten if reporting value is not clearly quantified.',
    suggestedAction: 'Prepare a renewal-focused brief with usage proof points and risk mitigation.',
  },
  {
    id: 'event-3',
    customerId: 'northstar-retail',
    date: '2026-07-05',
    eventType: 'Usage',
    source: 'Product Analytics',
    title: 'Collaboration usage grew 48%',
    summary: 'Store operations teams adopted shared channels and workflow approvals at a fast pace.',
    businessImpact: 'The account is ready for a broader expansion discussion.',
    suggestedAction: 'Frame the next meeting around scale, governance, and premium workflow capabilities.',
  },
  {
    id: 'event-4',
    customerId: 'northstar-retail',
    date: '2026-06-30',
    eventType: 'Meeting',
    source: 'Market News',
    title: 'Northstar announced new regional stores',
    summary: 'The company plans to open new locations in three regions during the next two quarters.',
    businessImpact: 'New teams may need onboarding, collaboration templates, and additional seats.',
    suggestedAction: 'Ask about rollout timing and whether store launch teams need standardized playbooks.',
  },
  {
    id: 'event-5',
    customerId: 'greenhealth-group',
    date: '2026-07-03',
    eventType: 'Meeting',
    source: 'Customer Success Notes',
    title: 'Pilot team requested executive dashboard examples',
    summary: 'The analytics pilot team asked for examples that show patient access and operational KPIs.',
    businessImpact: 'Value story is still being formed and needs executive-friendly proof points.',
    suggestedAction: 'Generate a discovery brief focused on success metrics and stakeholder alignment.',
  },
  {
    id: 'event-6',
    customerId: 'greenhealth-group',
    date: '2026-06-27',
    eventType: 'Meeting',
    source: 'Salesforce',
    title: 'Opportunity marked as discovery',
    summary: 'The account team added clinical operations and finance leaders as potential stakeholders.',
    businessImpact: 'The next meeting should clarify buying criteria and pilot success thresholds.',
    suggestedAction: 'Prepare questions around measurable outcomes, adoption blockers, and decision process.',
  },
]

const meetingTypes = ['QBR', 'Renewal', 'Discovery', 'Upsell']
const products = ['CRM Platform', 'Collaboration Tool', 'Business Analytics Software']
const deliverables = ['Call Brief', 'Email Draft', 'Meeting Agenda']
const timelineFilters = ['All', 'Meeting', 'Usage']

function App() {
  const [activeTab, setActiveTab] = useState('meeting')
  const [customers, setCustomers] = useState(initialCustomers)
  const [usageRecords, setUsageRecords] = useState(initialUsageRecords)
  const [lastDataUpload, setLastDataUpload] = useState('2026-07-05')
  const [selectedCustomerId, setSelectedCustomerId] = useState(initialCustomers[0].id)
  const [meetingType, setMeetingType] = useState(meetingTypes[0])
  const [product, setProduct] = useState(products[0])
  const [deliverable, setDeliverable] = useState(deliverables[0])
  const [notes, setNotes] = useState('')
  const [brief, setBrief] = useState(null)
  const [engagementLogs, setEngagementLogs] = useState([])
  const [intelligenceCustomerId, setIntelligenceCustomerId] = useState(initialCustomers[0].id)
  const [timelineFilter, setTimelineFilter] = useState('Meeting')

  const selectedCustomer = customers.find((customer) => customer.id === selectedCustomerId)
  const intelligenceCustomer = customers.find((customer) => customer.id === intelligenceCustomerId)

  const generatedBriefEvents = engagementLogs.map((log) => ({
    id: `generated-${log.id}`,
    customerId: log.customerId,
    date: log.date,
    eventType: 'Meeting',
    source: 'DealBrief AI',
    title: `${log.deliverable} generated for ${log.meetingType}`,
    summary: log.customerSnapshot,
    businessImpact: log.risksAndOpportunities.join(' '),
    suggestedAction: log.nextSteps[0],
  }))

  const timelineEvents = useMemo(
    () => [...generatedBriefEvents, ...baseTimelineEvents].sort((a, b) => new Date(b.date) - new Date(a.date)),
    [generatedBriefEvents],
  )

  const visibleTimelineEvents = timelineEvents.filter((event) => {
    const matchesCustomer = event.customerId === intelligenceCustomerId
    const matchesFilter = timelineFilter === 'All' || event.eventType === timelineFilter
    return matchesCustomer && matchesFilter
  })

  const handleGenerateBrief = () => {
    const nextBrief = createBrief({
      customer: selectedCustomer,
      meetingType,
      product,
      deliverable,
      notes,
    })

    setBrief(nextBrief)
  }

  const handleSaveBrief = () => {
    if (!brief) return

    const savedBrief = {
      ...brief,
      id: Date.now(),
      date: new Date().toISOString().slice(0, 10),
      generatedBy: 'DealBrief AI',
    }

    setEngagementLogs((previous) => [savedBrief, ...previous])
    setIntelligenceCustomerId(brief.customerId)
    setTimelineFilter('Meeting')
  }

  const handleCopyBrief = async () => {
    if (!brief) return

    const text = formatBriefForCopy(brief)

    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
    }
  }

  const handleCustomerCsvUpload = async (file) => {
    if (!file) return

    const rows = parseCsv(await file.text())
    const uploadedCustomers = rows
      .map((row) => {
        const name = getCsvValue(row, ['Customer Name', 'Customer', 'Name'])
        if (!name) return null

        return {
          id: slugify(name),
          name,
          industry: getCsvValue(row, ['Industry']) || 'Unknown',
          accountOwner: getCsvValue(row, ['Account Owner', 'Owner']) || 'Unassigned',
          salesforceId: getCsvValue(row, ['Salesforce Account ID', 'Salesforce ID', 'Account ID']) || `SF-${slugify(name).toUpperCase()}`,
          opportunityStage: getCsvValue(row, ['Opportunity Stage', 'Stage']) || 'Discovery',
          renewalDate: getCsvValue(row, ['Renewal Date']) || 'TBD',
          status: getCsvValue(row, ['Status']) || 'Active',
          usageGrowth: getCsvValue(row, ['Usage Growth']) || '+0%',
          licenseUtilization: getCsvValue(row, ['License Utilization']) || '0%',
          renewalRisk: getCsvValue(row, ['Renewal Risk']) || 'Medium',
          lastInteraction: getCsvValue(row, ['Last Interaction']) || 'No recent interaction',
          expansionSignal: getCsvValue(row, ['Expansion Signal']) || 'No expansion signal yet',
          nextBestAction: getCsvValue(row, ['Next Best Action']) || 'Review account data',
          signal:
            getCsvValue(row, ['AI Key Signal', 'Signal']) ||
            `${name} has newly uploaded customer data. Review usage, renewal risk, and account context before generating a brief.`,
        }
      })
      .filter(Boolean)

    if (uploadedCustomers.length === 0) return

    setCustomers((previous) => upsertById(previous, uploadedCustomers))
    setLastDataUpload(new Date().toLocaleDateString())
  }

  const handleUsageCsvUpload = async (file) => {
    if (!file) return

    const rows = parseCsv(await file.text())
    const uploadedUsageRecords = rows
      .map((row) => {
        const customerName = getCsvValue(row, ['Customer', 'Customer Name'])
        const productName = getCsvValue(row, ['Product'])
        if (!customerName || !productName) return null

        return {
          id: `usage-${slugify(customerName)}-${slugify(productName)}`,
          customerId: slugify(customerName),
          customerName,
          product: productName,
          activeUsers: getCsvValue(row, ['Active Users']) || '0',
          licenseUtilization: getCsvValue(row, ['License Utilization']) || '0%',
          usageGrowth: getCsvValue(row, ['Usage Growth']) || '+0%',
          featureAdoption: getCsvValue(row, ['Feature Adoption']) || 'Not available',
          lastUpdated: getCsvValue(row, ['Last Updated']) || new Date().toISOString().slice(0, 10),
        }
      })
      .filter(Boolean)

    if (uploadedUsageRecords.length === 0) return

    setUsageRecords((previous) => upsertById(previous, uploadedUsageRecords))
    setLastDataUpload(new Date().toLocaleDateString())
  }

  return (
    <div className="app">
      <header className="hero-section">
        <p className="eyebrow">AI Sales Meeting Brief Platform</p>
        <h1>DealBrief AI</h1>
        <p>Turn customer intelligence into sales-ready meeting briefs, email drafts, and meeting agendas.</p>
      </header>

      <div className="tabs-container">
        <nav className="tabs-nav" aria-label="DealBrief AI sections">
          <TabButton active={activeTab === 'meeting'} onClick={() => setActiveTab('meeting')}>
            Meeting Brief
          </TabButton>
          <TabButton active={activeTab === 'intelligence'} onClick={() => setActiveTab('intelligence')}>
            Customer Intelligence
          </TabButton>
          <TabButton active={activeTab === 'admin'} onClick={() => setActiveTab('admin')}>
            Admin Data Management
          </TabButton>
        </nav>

        <main className="tabs-content">
          {activeTab === 'meeting' && (
            <MeetingBriefPage
              customers={customers}
              selectedCustomerId={selectedCustomerId}
              setSelectedCustomerId={setSelectedCustomerId}
              meetingType={meetingType}
              setMeetingType={setMeetingType}
              product={product}
              setProduct={setProduct}
              deliverable={deliverable}
              setDeliverable={setDeliverable}
              notes={notes}
              setNotes={setNotes}
              brief={brief}
              onGenerate={handleGenerateBrief}
              onSave={handleSaveBrief}
              onCopy={handleCopyBrief}
            />
          )}

          {activeTab === 'intelligence' && (
            <CustomerIntelligencePage
              customers={customers}
              selectedCustomerId={intelligenceCustomerId}
              setSelectedCustomerId={setIntelligenceCustomerId}
              customer={intelligenceCustomer}
              timelineFilter={timelineFilter}
              setTimelineFilter={setTimelineFilter}
              timelineEvents={visibleTimelineEvents}
            />
          )}

          {activeTab === 'admin' && (
            <AdminDataManagementPage
              customers={customers}
              usageRecords={usageRecords}
              engagementLogs={engagementLogs}
              lastDataUpload={lastDataUpload}
              onCustomerCsvUpload={handleCustomerCsvUpload}
              onUsageCsvUpload={handleUsageCsvUpload}
            />
          )}
        </main>
      </div>
    </div>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button className={`tab-button ${active ? 'active' : ''}`} onClick={onClick}>
      {children}
    </button>
  )
}

function MeetingBriefPage({
  customers,
  selectedCustomerId,
  setSelectedCustomerId,
  meetingType,
  setMeetingType,
  product,
  setProduct,
  deliverable,
  setDeliverable,
  notes,
  setNotes,
  brief,
  onGenerate,
  onSave,
  onCopy,
}) {
  return (
    <section className="page-section">
      <div className="section-heading">
        <span>Core workflow</span>
        <h2>Generate a sales meeting brief</h2>
        <p>Select the customer context and DealBrief AI will assemble a mock, sales-ready brief below the form.</p>
      </div>

      <div className="panel">
        <div className="form-grid">
          <SelectField label="Customer" value={selectedCustomerId} onChange={setSelectedCustomerId}>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name}
              </option>
            ))}
          </SelectField>

          <SelectField label="Meeting Type" value={meetingType} onChange={setMeetingType}>
            {meetingTypes.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </SelectField>

          <SelectField label="Product Focus" value={product} onChange={setProduct}>
            {products.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </SelectField>

          <SelectField label="Deliverable Type" value={deliverable} onChange={setDeliverable}>
            {deliverables.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </SelectField>

          <label className="field field-full">
            Optional Notes
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Example: focus on renewal risk, expansion blockers, or executive audience needs"
              rows="4"
            />
          </label>
        </div>

        <button className="btn-primary" onClick={onGenerate}>
          Generate Meeting Brief
        </button>
      </div>

      {brief && <BriefResult brief={brief} onSave={onSave} onCopy={onCopy} />}
    </section>
  )
}

function CustomerIntelligencePage({
  customers,
  selectedCustomerId,
  setSelectedCustomerId,
  customer,
  timelineFilter,
  setTimelineFilter,
  timelineEvents,
}) {
  const cards = [
    ['Industry', customer.industry],
    ['Opportunity Stage', customer.opportunityStage],
    ['Usage Growth', customer.usageGrowth],
    ['License Utilization', customer.licenseUtilization],
    ['Renewal Risk', customer.renewalRisk],
    ['Last Interaction', customer.lastInteraction],
    ['Expansion Signal', customer.expansionSignal],
    ['Next Best Action', customer.nextBestAction],
  ]

  return (
    <section className="page-section">
      <div className="section-heading">
        <span>Customer context</span>
        <h2>Customer Intelligence</h2>
        <p>Review account health, AI signals, and timeline activity before generating the next meeting brief.</p>
      </div>

      <div className="panel">
        <SelectField
          label="Customer"
          value={selectedCustomerId}
          onChange={setSelectedCustomerId}
          className="centered-customer-select"
        >
          {customers.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </SelectField>

        <div className="summary-grid">
          {cards.map(([label, value]) => (
            <div className="summary-card" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="signal-card">
        <span>AI Key Signals</span>
        <p>{customer.signal}</p>
      </div>

      <div className="panel">
        <div className="timeline-header">
          <div>
            <h3>Customer Intelligence Timeline</h3>
            <p>Mock signals organized into meeting activity and product usage updates.</p>
          </div>
          <div className="filter-buttons">
            {timelineFilters.map((filter) => (
              <button
                key={filter}
                className={`filter-button ${timelineFilter === filter ? 'active' : ''}`}
                onClick={() => setTimelineFilter(filter)}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        <div className="timeline">
          {timelineEvents.length === 0 ? (
            <p className="empty-state">No timeline events match this filter yet.</p>
          ) : (
            timelineEvents.map((event) => <TimelineItem key={event.id} event={event} />)
          )}
        </div>
      </div>
    </section>
  )
}

function AdminDataManagementPage({
  customers,
  usageRecords,
  engagementLogs,
  lastDataUpload,
  onCustomerCsvUpload,
  onUsageCsvUpload,
}) {
  return (
    <section className="page-section">
      <div className="section-heading">
        <span>Data center</span>
        <h2>Admin Data Management</h2>
        <p>Manage the mock customer, usage, and engagement data that powers DealBrief AI brief generation.</p>
      </div>

      <div className="overview-grid">
        <MetricCard label="Total Customers" value={customers.length} />
        <MetricCard label="Usage Records" value={usageRecords.length} />
        <MetricCard label="Engagement Logs" value={engagementLogs.length} />
        <MetricCard label="Last Data Upload" value={lastDataUpload} />
      </div>

      <div className="panel upload-panel">
        <div>
          <h3>Upload Data</h3>
          <p>Upload CSV files to update this session’s customer and usage data. Backend persistence can be added later.</p>
        </div>
        <div className="upload-actions">
          <label className="btn-secondary file-upload-button">
            Upload Customer CSV
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                onCustomerCsvUpload(event.target.files[0])
                event.target.value = ''
              }}
            />
          </label>
          <label className="btn-secondary file-upload-button">
            Upload Usage CSV
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                onUsageCsvUpload(event.target.files[0])
                event.target.value = ''
              }}
            />
          </label>
        </div>
      </div>

      <DataTable title="Manage Customers" columns={['Customer Name', 'Industry', 'Account Owner', 'Salesforce Account ID', 'Opportunity Stage', 'Renewal Date', 'Status', 'Action']}>
        {customers.map((customer) => (
          <tr key={customer.id}>
            <td>{customer.name}</td>
            <td>{customer.industry}</td>
            <td>{customer.accountOwner}</td>
            <td>{customer.salesforceId}</td>
            <td>{customer.opportunityStage}</td>
            <td>{customer.renewalDate}</td>
            <td><span className="status-pill">{customer.status}</span></td>
            <td><button className="table-action">Delete</button></td>
          </tr>
        ))}
      </DataTable>

      <DataTable title="Manage Usage Data" columns={['Customer', 'Product', 'Active Users', 'License Utilization', 'Usage Growth', 'Feature Adoption', 'Last Updated', 'Action']}>
        {usageRecords.map((record) => {
          const customer = customers.find((item) => item.id === record.customerId)

          return (
            <tr key={record.id}>
              <td>{customer?.name || record.customerName || record.customerId}</td>
              <td>{record.product}</td>
              <td>{record.activeUsers}</td>
              <td>{record.licenseUtilization}</td>
              <td>{record.usageGrowth}</td>
              <td>{record.featureAdoption}</td>
              <td>{record.lastUpdated}</td>
              <td><button className="table-action">Delete</button></td>
            </tr>
          )
        })}
      </DataTable>

      <DataTable title="Manage Engagement Log" columns={['Date', 'Customer', 'Meeting Type', 'Product', 'Deliverable', 'Generated By', 'Action']}>
        {engagementLogs.length === 0 ? (
          <tr>
            <td colSpan="7" className="empty-table">No saved meeting briefs yet.</td>
          </tr>
        ) : (
          engagementLogs.map((log) => (
            <tr key={log.id}>
              <td>{log.date}</td>
              <td>{log.customerName}</td>
              <td>{log.meetingType}</td>
              <td>{log.product}</td>
              <td>{log.deliverable}</td>
              <td>{log.generatedBy}</td>
              <td><button className="table-action">Delete</button></td>
            </tr>
          ))
        )}
      </DataTable>
    </section>
  )
}

function SelectField({ label, value, onChange, children, className = '' }) {
  return (
    <label className={`field ${className}`}>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
    </label>
  )
}

function BriefResult({ brief, onSave, onCopy }) {
  const isEmailDraft = brief.deliverable === 'Email Draft'
  const isMeetingAgenda = brief.deliverable === 'Meeting Agenda'

  return (
    <section className="panel brief-result">
      <div className="result-title">
        <div>
          <span>{brief.deliverable}</span>
          <h2>{brief.title}</h2>
        </div>
        <p>{brief.meetingType} · {brief.product}</p>
      </div>

      {isEmailDraft ? (
        <EmailDraftResult brief={brief} />
      ) : isMeetingAgenda ? (
        <MeetingAgendaResult brief={brief} />
      ) : (
        <CallBriefResult brief={brief} />
      )}

      <div className="result-actions">
        <button className="btn-primary" onClick={onSave}>Save to Engagement Log</button>
        <button className="btn-secondary" onClick={onCopy}>Copy Brief</button>
      </div>
    </section>
  )
}

function CallBriefResult({ brief }) {
  return (
    <>
      <BriefSection title="Customer Snapshot" content={brief.customerSnapshot} />
      <BriefSection title="Key Insights" items={brief.keyInsights} />
      <BriefSection title="Talking Points" items={brief.talkingPoints} />
      <BriefSection title="Suggested Questions" items={brief.suggestedQuestions} />
      <BriefSection title="Risks and Opportunities" items={brief.risksAndOpportunities} />
      <BriefSection title="Recommended Next Steps" items={brief.nextSteps} />
    </>
  )
}

function EmailDraftResult({ brief }) {
  return (
    <div className="email-draft-card">
      <div className="email-line"><strong>To:</strong> {brief.email.to}</div>
      <div className="email-line"><strong>Subject:</strong> {brief.email.subject}</div>
      <div className="email-body">
        <p>{brief.email.greeting}</p>
        {brief.email.paragraphs.map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
        <p>{brief.email.callToAction}</p>
        <p className="email-signature">{brief.email.signature}</p>
      </div>
    </div>
  )
}

function MeetingAgendaResult({ brief }) {
  return (
    <>
      <div className="agenda-overview">
        <BriefSection title="Meeting Objective" content={brief.agenda.objective} />
        <BriefSection title="Desired Outcome" content={brief.agenda.desiredOutcome} />
      </div>
      <div className="agenda-list">
        {brief.agenda.items.map((item, index) => (
          <div className="agenda-row" key={index}>
            <span>{item.time}</span>
            <div>
              <h3>{item.topic}</h3>
              <p>{item.detail}</p>
            </div>
          </div>
        ))}
      </div>
      <BriefSection title="Preparation Notes" items={brief.agenda.preparation} />
    </>
  )
}

function BriefSection({ title, content, items }) {
  return (
    <div className="brief-section">
      <h3>{title}</h3>
      {content && <p>{content}</p>}
      {items && (
        <ul>
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function TimelineItem({ event }) {
  return (
    <article className="timeline-item">
      <div className="timeline-date">
        <strong>{event.date}</strong>
        <span>{event.eventType}</span>
      </div>
      <div className="timeline-body">
        <p className="timeline-source">{event.source}</p>
        <h4>{event.title}</h4>
        <p>{event.summary}</p>
        <div className="impact-grid">
          <div>
            <span>Business Impact</span>
            <p>{event.businessImpact}</p>
          </div>
          <div>
            <span>Suggested Action</span>
            <p>{event.suggestedAction}</p>
          </div>
        </div>
      </div>
    </article>
  )
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function DataTable({ title, columns, children }) {
  return (
    <section className="panel table-panel">
      <h3>{title}</h3>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>{children}</tbody>
        </table>
      </div>
    </section>
  )
}

function createBrief({ customer, meetingType, product, deliverable, notes }) {
  const productAngle = {
    'CRM Platform': 'pipeline visibility, account handoffs, and automated follow-up discipline',
    'Collaboration Tool': 'cross-team coordination, workflow standardization, and faster field execution',
    'Business Analytics Software': 'executive visibility, KPI alignment, and faster operating decisions',
  }[product]

  const meetingAngle = {
    QBR: 'prove business value and identify the next value milestone',
    Renewal: 'reduce renewal risk and make the commercial value case explicit',
    Discovery: 'clarify priorities, stakeholders, buying criteria, and success metrics',
    Upsell: 'connect current adoption momentum to a credible expansion path',
  }[meetingType]

  const baseBrief = {
    customerId: customer.id,
    customerName: customer.name,
    meetingType,
    product,
    deliverable,
    notes,
    title: `${customer.name} ${deliverable}`,
    customerSnapshot:
      `${customer.name} is a ${customer.industry.toLowerCase()} account in ${customer.opportunityStage}. Current usage growth is ${customer.usageGrowth}, license utilization is ${customer.licenseUtilization}, and renewal risk is ${customer.renewalRisk.toLowerCase()}.`,
    keyInsights: [
      `${product} conversations should emphasize ${productAngle}.`,
      `This ${meetingType} should ${meetingAngle}.`,
      notes ? `User-provided context to incorporate: ${notes}` : 'No additional notes were provided, so the brief prioritizes usage, renewal, and stakeholder signals.',
    ],
    talkingPoints: [
      `Open with the latest adoption signal: ${customer.usageGrowth} usage growth and ${customer.licenseUtilization} license utilization.`,
      `Connect ${product} value to the customer’s current ${customer.opportunityStage.toLowerCase()} motion.`,
      `Ask how the customer measures success for ${productAngle}.`,
    ],
    suggestedQuestions: [
      `What changed internally that is driving the current ${product} usage pattern?`,
      `Which teams or leaders need to see proof of value before the next decision?`,
      `What would make this ${meetingType.toLowerCase()} feel successful from the customer’s perspective?`,
    ],
    risksAndOpportunities: [
      `Risk: ${customer.renewalRisk} renewal risk could create friction if value is not quantified clearly.`,
      `Opportunity: ${customer.usageGrowth} growth suggests room to expand adoption or package additional services.`,
      `Opportunity: A ${deliverable} can align stakeholders around a concrete next step.`,
    ],
    nextSteps: [
      `Send a concise follow-up summarizing ${product} value, open questions, and owners.`,
      `Confirm the next meeting date and include stakeholders tied to ${customer.opportunityStage}.`,
      `Prepare one proof point that links product adoption to a measurable business outcome.`,
    ],
  }

  if (deliverable === 'Email Draft') {
    return {
      ...baseBrief,
      title: `${customer.name} Email Draft`,
      keyInsights: [
        `Lead with a concise value message around ${productAngle}.`,
        `Position the email as a follow-up for the ${meetingType} conversation.`,
        notes ? `Include this context naturally: ${notes}` : 'Keep the email short and focused on next-step alignment.',
      ],
      email: {
        to: `${customer.name} stakeholder team`,
        subject: `${meetingType} follow-up: ${product} priorities and next steps`,
        greeting: `Hi ${customer.name} team,`,
        paragraphs: [
          `Thank you for taking the time to discuss your ${product} priorities. Based on the latest account signals, ${customer.name} is seeing ${customer.usageGrowth} usage growth with ${customer.licenseUtilization} license utilization.`,
          `For the next conversation, we recommend focusing on ${productAngle} so the team can connect current adoption to measurable business outcomes.`,
          `Given the current ${customer.opportunityStage.toLowerCase()} stage, the main areas to align on are stakeholder priorities, renewal risk, and the clearest path to value.`,
        ],
        callToAction: `Would you be open to a short follow-up meeting to confirm priorities and agree on next steps for ${product}?`,
        signature: 'Best,\nDealBrief AI Account Team',
      },
    }
  }

  if (deliverable === 'Meeting Agenda') {
    return {
      ...baseBrief,
      title: `${customer.name} Meeting Agenda`,
      keyInsights: [
        `Use the meeting to ${meetingAngle}.`,
        `Anchor the discussion in ${customer.usageGrowth} usage growth and ${customer.licenseUtilization} license utilization.`,
        notes ? `Reserve time to address this note: ${notes}` : 'Reserve time to confirm open questions and decision criteria.',
      ],
      agenda: {
        objective: `Align on ${customer.name}'s ${product} priorities and define the next step for the ${meetingType} motion.`,
        desiredOutcome: 'A shared action plan with owners, timing, and the next customer commitment.',
        items: [
          {
            time: '5 min',
            topic: 'Opening and meeting goals',
            detail: `Confirm what ${customer.name} wants to accomplish in the ${meetingType} discussion.`,
          },
          {
            time: '10 min',
            topic: 'Customer snapshot review',
            detail: `Review usage growth, license utilization, renewal risk, and recent interactions.`,
          },
          {
            time: '15 min',
            topic: `${product} priorities`,
            detail: `Discuss how ${productAngle} maps to current business goals.`,
          },
          {
            time: '10 min',
            topic: 'Risks, opportunities, and blockers',
            detail: 'Identify stakeholder concerns, adoption gaps, expansion signals, and timing risks.',
          },
          {
            time: '5 min',
            topic: 'Decisions and next steps',
            detail: 'Confirm owners, action items, and the date for the next follow-up.',
          },
        ],
        preparation: [
          'Bring the latest usage and adoption metrics.',
          `Prepare one customer-specific proof point for ${product}.`,
          'Confirm who owns the next decision and what information they need.',
        ],
      },
    }
  }

  return {
    ...baseBrief,
    title: `${customer.name} Call Brief`,
    keyInsights: [
      `${product} conversations should emphasize ${productAngle}.`,
      `This ${meetingType} should ${meetingAngle}.`,
      'Keep the conversation focused, consultative, and action-oriented.',
      notes ? `User-provided context to incorporate: ${notes}` : 'No additional notes were provided, so the brief prioritizes usage, renewal, and stakeholder signals.',
    ],
  }
}

function formatBriefForCopy(brief) {
  if (brief.deliverable === 'Email Draft') {
    return [
      `To: ${brief.email.to}`,
      `Subject: ${brief.email.subject}`,
      '',
      brief.email.greeting,
      ...brief.email.paragraphs,
      brief.email.callToAction,
      brief.email.signature,
    ].join('\n\n')
  }

  if (brief.deliverable === 'Meeting Agenda') {
    return [
      brief.title,
      '',
      `Objective: ${brief.agenda.objective}`,
      `Desired Outcome: ${brief.agenda.desiredOutcome}`,
      '',
      'Agenda',
      ...brief.agenda.items.map((item) => `- ${item.time}: ${item.topic} — ${item.detail}`),
      '',
      'Preparation Notes',
      ...brief.agenda.preparation.map((item) => `- ${item}`),
    ].join('\n')
  }

  const sections = [
    ['Customer Snapshot', [brief.customerSnapshot]],
    ['Key Insights', brief.keyInsights],
    ['Talking Points', brief.talkingPoints],
    ['Suggested Questions', brief.suggestedQuestions],
    ['Risks and Opportunities', brief.risksAndOpportunities],
    ['Recommended Next Steps', brief.nextSteps],
  ]

  return sections
    .map(([title, items]) => `${title}\n${items.map((item) => `- ${item}`).join('\n')}`)
    .join('\n\n')
}

function parseCsv(csvText) {
  const rows = []
  let currentRow = []
  let currentValue = ''
  let insideQuotes = false

  for (let index = 0; index < csvText.length; index += 1) {
    const char = csvText[index]
    const nextChar = csvText[index + 1]

    if (char === '"' && insideQuotes && nextChar === '"') {
      currentValue += '"'
      index += 1
    } else if (char === '"') {
      insideQuotes = !insideQuotes
    } else if (char === ',' && !insideQuotes) {
      currentRow.push(currentValue.trim())
      currentValue = ''
    } else if ((char === '\n' || char === '\r') && !insideQuotes) {
      if (char === '\r' && nextChar === '\n') index += 1
      currentRow.push(currentValue.trim())
      if (currentRow.some(Boolean)) rows.push(currentRow)
      currentRow = []
      currentValue = ''
    } else {
      currentValue += char
    }
  }

  currentRow.push(currentValue.trim())
  if (currentRow.some(Boolean)) rows.push(currentRow)

  if (rows.length < 2) return []

  const headers = rows[0].map(normalizeHeader)

  return rows.slice(1).map((row) => {
    return headers.reduce((record, header, index) => {
      record[header] = row[index] || ''
      return record
    }, {})
  })
}

function getCsvValue(row, possibleHeaders) {
  for (const header of possibleHeaders) {
    const value = row[normalizeHeader(header)]
    if (value) return value
  }

  return ''
}

function normalizeHeader(header) {
  return header.toLowerCase().replace(/[^a-z0-9]/g, '')
}

function slugify(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

function upsertById(existingItems, incomingItems) {
  const itemMap = new Map(existingItems.map((item) => [item.id, item]))

  incomingItems.forEach((item) => {
    itemMap.set(item.id, { ...itemMap.get(item.id), ...item })
  })

  return Array.from(itemMap.values())
}

export default App
