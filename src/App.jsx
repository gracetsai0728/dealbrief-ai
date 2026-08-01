import { useEffect, useState } from 'react'
import {
  deleteCustomer,
  deleteEngagement,
  deleteUsage,
  fetchCustomerDashboard,
  fetchCustomers,
  fetchEngagementLog,
  fetchImportJobs,
  fetchProducts,
  fetchUsage,
  generateBrief,
  importCustomers,
  importUsage,
  refreshIntelligence,
  saveBrief,
} from './api'
import { DELIVERABLES, MEETING_TYPES } from './constants'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('meeting')
  const [customers, setCustomers] = useState([])
  const [products, setProducts] = useState([])
  const [usageRecords, setUsageRecords] = useState([])
  const [engagementLogs, setEngagementLogs] = useState([])
  const [importJobs, setImportJobs] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [selectedCustomerId, setSelectedCustomerId] = useState('')
  const [intelligenceCustomerId, setIntelligenceCustomerId] = useState('')
  const [meetingType, setMeetingType] = useState(MEETING_TYPES[0])
  const [productId, setProductId] = useState('')
  const [deliverable, setDeliverable] = useState(DELIVERABLES[0])
  const [notes, setNotes] = useState('')
  const [brief, setBrief] = useState(null)
  const [busyAction, setBusyAction] = useState('')
  const [notice, setNotice] = useState(null)

  const loadData = async () => {
    const [customerData, productData, usageData, engagementData, importData] =
      await Promise.all([
        fetchCustomers(),
        fetchProducts(),
        fetchUsage(),
        fetchEngagementLog(),
        fetchImportJobs(),
      ])
    setCustomers(customerData)
    setProducts(productData)
    setUsageRecords(usageData)
    setEngagementLogs(engagementData)
    setImportJobs(importData)
    setSelectedCustomerId((current) =>
      customerData.some((item) => item.id === current) ? current : customerData[0]?.id || '',
    )
    setIntelligenceCustomerId((current) =>
      customerData.some((item) => item.id === current) ? current : customerData[0]?.id || '',
    )
    setProductId((current) =>
      productData.some((item) => item.id === current) ? current : productData[0]?.id || '',
    )
  }

  useEffect(() => {
    setBusyAction('initial-load')
    loadData()
      .catch((error) => setNotice({ tab: 'meeting', type: 'error', text: error.message }))
      .finally(() => setBusyAction(''))
  }, [])

  useEffect(() => {
    if (!intelligenceCustomerId) {
      setDashboard(null)
      return
    }
    fetchCustomerDashboard(intelligenceCustomerId)
      .then(setDashboard)
      .catch((error) => setNotice({ tab: 'intelligence', type: 'error', text: error.message }))
  }, [intelligenceCustomerId])

  const lastDataUpload = importJobs[0]?.completedAt || importJobs[0]?.createdAt

  const runAction = async (name, action, successMessage, reload = true) => {
    const noticeTab = activeTab
    setBusyAction(name)
    setNotice(null)
    try {
      const result = await action()
      if (reload) await loadData()
      setNotice({ tab: noticeTab, type: 'success', text: successMessage })
      return result
    } catch (error) {
      setNotice({ tab: noticeTab, type: 'error', text: error.message })
      return null
    } finally {
      setBusyAction('')
    }
  }

  const handleGenerateBrief = async () => {
    if (!selectedCustomerId || !productId) return
    const result = await runAction(
      'generate',
      () =>
        generateBrief({
          customerId: selectedCustomerId,
          productId,
          meetingType: meetingType.toLowerCase(),
          deliverableType: deliverable.toLowerCase().replaceAll(' ', '_'),
          notes,
        }),
      'Meeting brief generated as a draft.',
      false,
    )
    if (result) setBrief(result)
  }

  const handleSaveBrief = async () => {
    if (!brief?.engagementId) return
    const saved = await runAction(
      'save',
      () => saveBrief(brief.engagementId),
      'Brief saved to the customer engagement timeline.',
    )
    if (saved) {
      setBrief((current) => ({ ...current, status: 'saved' }))
      setIntelligenceCustomerId(brief.customerId)
      setDashboard(await fetchCustomerDashboard(brief.customerId))
    }
  }

  const handleCopyBrief = async () => {
    if (!brief || !navigator.clipboard) return
    await navigator.clipboard.writeText(formatBriefForCopy(brief))
    setNotice({ tab: 'meeting', type: 'success', text: 'Brief copied to the clipboard.' })
  }

  const handleCsvUpload = async (file, importType) => {
    if (!file) return
    const rows = parseCsv(await file.text())
    if (!rows.length) {
      setNotice({ tab: 'admin', type: 'error', text: 'The CSV contains no data rows.' })
      return
    }
    const importer = importType === 'customers' ? importCustomers : importUsage
    await runAction(
      `import-${importType}`,
      () => importer(file.name, rows),
      `${importType === 'customers' ? 'Customer' : 'Usage'} import completed.`,
    )
  }

  const handleRefreshIntelligence = async () => {
    if (!intelligenceCustomerId) return
    const result = await runAction(
      'intelligence',
      () => refreshIntelligence(intelligenceCustomerId),
      'A new AI intelligence snapshot was saved.',
      false,
    )
    if (result) setDashboard(await fetchCustomerDashboard(intelligenceCustomerId))
  }

  const handleDelete = async (kind, id, label) => {
    if (!window.confirm(`Delete ${label}?`)) return
    const operations = {
      customer: deleteCustomer,
      usage: deleteUsage,
      engagement: deleteEngagement,
    }
    await runAction(
      `delete-${kind}-${id}`,
      () => operations[kind](id),
      `${label} deleted.`,
    )
    if (intelligenceCustomerId) {
      fetchCustomerDashboard(intelligenceCustomerId).then(setDashboard).catch(() => setDashboard(null))
    }
  }

  return (
    <div className="app">
      <header className="hero-section">
        <p className="eyebrow"><span className="hero-spark" aria-hidden="true">✦</span> AI Sales Meeting Brief Platform</p>
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
            Data Management
          </TabButton>
        </nav>

        {notice?.tab === activeTab && (
          <div className={`api-notice ${notice.type}`}>{notice.text}</div>
        )}
        {busyAction === 'initial-load' ? (
          <p className="loading-state">Loading data from Flask and PostgreSQL…</p>
        ) : (
          <main className="tabs-content">
            {activeTab === 'meeting' && (
              <MeetingBriefPage
                customers={customers}
                products={products}
                selectedCustomerId={selectedCustomerId}
                setSelectedCustomerId={setSelectedCustomerId}
                meetingType={meetingType}
                setMeetingType={setMeetingType}
                productId={productId}
                setProductId={setProductId}
                deliverable={deliverable}
                setDeliverable={setDeliverable}
                notes={notes}
                setNotes={setNotes}
                brief={brief}
                busyAction={busyAction}
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
                dashboard={dashboard}
                busy={busyAction === 'intelligence'}
                onRefresh={handleRefreshIntelligence}
              />
            )}

            {activeTab === 'admin' && (
              <AdminDataManagementPage
                customers={customers}
                usageRecords={usageRecords}
                engagementLogs={engagementLogs}
                lastDataUpload={lastDataUpload}
                busyAction={busyAction}
                onCustomerCsvUpload={(file) => handleCsvUpload(file, 'customers')}
                onUsageCsvUpload={(file) => handleCsvUpload(file, 'usage')}
                onDelete={handleDelete}
              />
            )}
          </main>
        )}
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
  products,
  selectedCustomerId,
  setSelectedCustomerId,
  meetingType,
  setMeetingType,
  productId,
  setProductId,
  deliverable,
  setDeliverable,
  notes,
  setNotes,
  brief,
  busyAction,
  onGenerate,
  onSave,
  onCopy,
}) {
  return (
    <section className="page-section meeting-page">
      <div className="section-heading">
        <h2>Meeting Brief</h2>
      </div>

      <div className="panel meeting-form-panel">
        <div className="form-grid">
          <SelectField label="Customer" value={selectedCustomerId} onChange={setSelectedCustomerId}>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>{customer.name}</option>
            ))}
          </SelectField>
          <SelectField label="Meeting Type" value={meetingType} onChange={setMeetingType}>
            {MEETING_TYPES.map((item) => <option key={item}>{item}</option>)}
          </SelectField>
          <SelectField label="Product Focus" value={productId} onChange={setProductId}>
            {products.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </SelectField>
          <SelectField label="Deliverable Type" value={deliverable} onChange={setDeliverable}>
            {DELIVERABLES.map((item) => <option key={item}>{item}</option>)}
          </SelectField>
          <label className="field field-full">
            Optional Notes
            <textarea
              value={notes}
              maxLength="2000"
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Example: focus on renewal planning or executive audience needs"
              rows="4"
            />
          </label>
        </div>
        <button
          className="btn-primary"
          disabled={!selectedCustomerId || !productId || busyAction === 'generate'}
          onClick={onGenerate}
        >
          {busyAction === 'generate' ? 'Generating Brief…' : 'Generate Meeting Brief'}
        </button>
      </div>

      {brief && (
        <BriefResult
          brief={brief}
          saving={busyAction === 'save'}
          onSave={onSave}
          onCopy={onCopy}
        />
      )}
    </section>
  )
}

function CustomerIntelligencePage({
  customers,
  selectedCustomerId,
  setSelectedCustomerId,
  dashboard,
  busy,
  onRefresh,
}) {
  const customer = dashboard?.customer
  const intelligence = dashboard?.intelligence
  const latestUsage = dashboard?.latestUsage || []
  const primaryUsage = latestUsage[0]
  const cards = [
    ['Industry', customer?.industry || 'Not available'],
    ['Usage Growth', formatPercent(primaryUsage?.usageGrowth)],
    ['License Utilization', formatPercent(primaryUsage?.licenseUtilization)],
    ['Renewal Date', formatDate(customer?.renewalDate)],
    ['Last Interaction', formatDate(intelligence?.sourceDataThrough)],
    ['Active Users', primaryUsage?.activeUsers ?? 'Not available'],
  ]

  return (
    <section className="page-section intelligence-page">
      <div className="section-heading">
        <h2>Customer Intelligence</h2>
      </div>

      <div className="panel intelligence-panel">
        <IntelligenceSectionHeader
          title="Customer Overview"
          subtitle="Latest customer profile, product usage, and account activity."
        />
        <div className="intelligence-controls">
          <SelectField
            className="centered-customer-select"
            label="Customer"
            value={selectedCustomerId}
            onChange={setSelectedCustomerId}
          >
            {customers.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </SelectField>
          <button className="btn-secondary" disabled={!selectedCustomerId || busy} onClick={onRefresh}>
            {busy ? 'Analyzing…' : 'Refresh AI Intelligence'}
          </button>
        </div>
        <div className="summary-grid">
          {cards.map(([label, value]) => (
            <div className="summary-card" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="panel timeline-panel">
        <IntelligenceSectionHeader
          title="Customer Engagement Timeline"
          subtitle="Meeting history from generated briefs saved to the engagement log."
        />
        <div className="timeline">
          {dashboard?.engagementTimeline?.length ? (
            dashboard.engagementTimeline.map((event) => <TimelineItem key={event.id} event={event} />)
          ) : (
            <p className="empty-state">No saved meeting briefs yet.</p>
          )}
        </div>
      </div>

      <div className="signal-card">
        <IntelligenceSectionHeader
          title="Next Best Action"
          subtitle="Recommended follow-up actions based on usage and saved meeting history."
        />
        {intelligence?.nextBestActions?.length ? (
          <ul>
            {intelligence.nextBestActions.map((action, index) => (
              <li key={`${action.action}-${index}`}>
                {action.action}
                {action.reason ? ` — ${action.reason}` : ''}
              </li>
            ))}
          </ul>
        ) : (
          <p>Refresh intelligence after usage or meeting data is available.</p>
        )}
      </div>
    </section>
  )
}

function AdminDataManagementPage({
  customers,
  usageRecords,
  engagementLogs,
  lastDataUpload,
  busyAction,
  onCustomerCsvUpload,
  onUsageCsvUpload,
  onDelete,
}) {
  return (
    <section className="page-section data-management-page">
      <div className="section-heading">
        <h2>Data Management</h2>
      </div>
      <div className="overview-grid">
        <MetricCard label="Total Customers" value={customers.length} />
        <MetricCard label="Usage Records" value={usageRecords.length} />
        <MetricCard label="Engagement Logs" value={engagementLogs.length} />
        <MetricCard label="Last Data Upload" value={formatDate(lastDataUpload)} />
      </div>

      <div className="panel upload-panel">
        <div>
          <h3>Upload Data</h3>
          <p>CSV rows are validated by Flask and tracked in the import_jobs table.</p>
        </div>
        <div className="upload-actions">
          <FileUploadButton
            label={busyAction === 'import-customers' ? 'Uploading…' : 'Upload Customer CSV'}
            disabled={busyAction === 'import-customers'}
            onFile={onCustomerCsvUpload}
          />
          <FileUploadButton
            label={busyAction === 'import-usage' ? 'Uploading…' : 'Upload Usage CSV'}
            disabled={busyAction === 'import-usage'}
            onFile={onUsageCsvUpload}
          />
        </div>
      </div>

      <DataTable tone="blue" title="Manage Customers" columns={['Customer Name', 'Industry', 'Account Owner', 'Salesforce Account ID', 'Opportunity Stage', 'Renewal Date', 'Status', 'Action']}>
        {customers.map((customer) => (
          <tr key={customer.id}>
            <td>{customer.name}</td>
            <td>{customer.industry || '—'}</td>
            <td>{customer.accountOwner?.name || 'Unassigned'}</td>
            <td>{customer.salesforceAccountId || '—'}</td>
            <td>{customer.opportunityStage || '—'}</td>
            <td>{formatDate(customer.renewalDate)}</td>
            <td><span className="status-pill">{titleCase(customer.status)}</span></td>
            <td>
              <button className="table-action" onClick={() => onDelete('customer', customer.id, customer.name)}>
                Delete
              </button>
            </td>
          </tr>
        ))}
      </DataTable>

      <DataTable tone="green" title="Manage Usage Data" columns={['Customer', 'Product', 'Active Users', 'License Utilization', 'Usage Growth', 'Feature Adoption', 'Snapshot Date', 'Action']}>
        {usageRecords.map((record) => (
          <tr key={record.id}>
            <td>{record.customerName || record.customerId}</td>
            <td>{record.productName}</td>
            <td>{record.activeUsers}</td>
            <td>{formatPercent(record.licenseUtilization)}</td>
            <td>{formatPercent(record.usageGrowth, true)}</td>
            <td>{formatFeatureAdoption(record.featureAdoption)}</td>
            <td>{formatDate(record.snapshotDate)}</td>
            <td>
              <button className="table-action" onClick={() => onDelete('usage', record.id, `${record.customerName} usage snapshot`)}>
                Delete
              </button>
            </td>
          </tr>
        ))}
      </DataTable>

      <DataTable tone="purple" title="Manage Engagement Log" columns={['Date', 'Customer', 'Meeting Type', 'Product', 'Deliverable', 'Generated By', 'Action']}>
        {engagementLogs.length ? engagementLogs.map((log) => (
          <tr key={log.id}>
            <td>{formatDate(log.date)}</td>
            <td>{log.customerName}</td>
            <td>{titleCase(log.meetingType)}</td>
            <td>{log.product || '—'}</td>
            <td>{titleCase(log.deliverableType?.replaceAll('_', ' '))}</td>
            <td>{log.generatedBy}</td>
            <td>
              <button className="table-action" onClick={() => onDelete('engagement', log.id, log.title)}>
                Delete
              </button>
            </td>
          </tr>
        )) : (
          <tr><td colSpan="7" className="empty-table">No saved meeting briefs yet.</td></tr>
        )}
      </DataTable>
    </section>
  )
}

function FileUploadButton({ label, disabled, onFile }) {
  return (
    <label className={`btn-secondary file-upload-button ${disabled ? 'disabled' : ''}`}>
      {label}
      <input
        type="file"
        accept=".csv,text/csv"
        disabled={disabled}
        onChange={(event) => {
          onFile(event.target.files[0])
          event.target.value = ''
        }}
      />
    </label>
  )
}

function SelectField({ className = '', label, value, onChange, children }) {
  return (
    <label className={`field ${className}`.trim()}>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
    </label>
  )
}

function BriefResult({ brief, saving, onSave, onCopy }) {
  const deliverableType = brief.deliverableType || brief.deliverable?.toLowerCase().replaceAll(' ', '_')
  return (
    <section className="result-panel">
      <div className="result-heading">
        <div>
          <span>{brief.meetingType} · {brief.product}</span>
          <h2>{brief.title}</h2>
          <p>{brief.summary}</p>
        </div>
        <span className="status-pill">{titleCase(brief.status)}</span>
      </div>

      {deliverableType === 'email_draft' ? (
        <EmailDraftResult brief={brief} />
      ) : deliverableType === 'meeting_agenda' ? (
        <MeetingAgendaResult brief={brief} />
      ) : (
        <CallBriefResult brief={brief} />
      )}
      <div className="result-actions">
        <button className="btn-primary" disabled={brief.status === 'saved' || saving} onClick={onSave}>
          {brief.status === 'saved' ? 'Saved to Engagement Log' : saving ? 'Saving…' : 'Save to Engagement Log'}
        </button>
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
        {brief.email.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}
        <p>{brief.email.callToAction}</p>
        <p className="email-signature">{brief.email.signature}</p>
      </div>
    </div>
  )
}

function MeetingAgendaResult({ brief }) {
  return (
    <>
      <BriefSection title="Meeting Objective" content={brief.agenda.objective} />
      <BriefSection title="Desired Outcome" content={brief.agenda.desiredOutcome} />
      <div className="agenda-list">
        {brief.agenda.items.map((item, index) => (
          <div className="agenda-row" key={index}>
            <span>{item.time}</span>
            <div><h3>{item.topic}</h3><p>{item.detail}</p></div>
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
      {items && <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul>}
    </div>
  )
}

function TimelineItem({ event }) {
  return (
    <article className="timeline-item">
      <div className="timeline-date">
        <strong>{formatDate(event.date)}</strong>
        <span>{titleCase(event.meetingType)}</span>
        <p>{event.product}</p>
      </div>
      <div className="timeline-body"><p>{event.meetingSummary || event.summary}</p></div>
    </article>
  )
}

function MetricCard({ label, value }) {
  return <div className="metric-card"><span>{label}</span><strong>{value || '—'}</strong></div>
}

function IntelligenceSectionHeader({ title, subtitle }) {
  return (
    <div className="intelligence-section-header">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </div>
  )
}

function DataTable({ title, tone = 'blue', columns, children }) {
  return (
    <details className={`panel table-panel table-panel-${tone}`}>
      <summary className="table-toggle">
        <h3>{title}</h3>
        <span className="table-toggle-icon" aria-hidden="true">⌄</span>
      </summary>
      <div className="table-scroll">
        <table>
          <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
          <tbody>{children}</tbody>
        </table>
      </div>
    </details>
  )
}

function parseCsv(text) {
  const lines = text.replace(/^\uFEFF/, '').split(/\r?\n/).filter((line) => line.trim())
  if (lines.length < 2) return []
  const headers = parseCsvLine(lines[0])
  return lines.slice(1).map((line) =>
    Object.fromEntries(headers.map((header, index) => [header.trim(), parseCsvLine(line)[index]?.trim() || ''])),
  )
}

function parseCsvLine(line) {
  const cells = []
  let current = ''
  let quoted = false
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index]
    if (character === '"' && quoted && line[index + 1] === '"') {
      current += '"'
      index += 1
    } else if (character === '"') {
      quoted = !quoted
    } else if (character === ',' && !quoted) {
      cells.push(current)
      current = ''
    } else {
      current += character
    }
  }
  cells.push(current)
  return cells
}

function formatBriefForCopy(brief) {
  return JSON.stringify(brief, null, 2)
}

function formatDate(value) {
  if (!value) return '—'
  const dateOnlyMatch = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/)
  const date = dateOnlyMatch
    ? new Date(
        Number(dateOnlyMatch[1]),
        Number(dateOnlyMatch[2]) - 1,
        Number(dateOnlyMatch[3]),
      )
    : new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString()
}

function formatPercent(value, signed = false) {
  if (value === null || value === undefined || value === '') return '—'
  return `${signed && Number(value) > 0 ? '+' : ''}${Number(value).toFixed(0)}%`
}

function formatFeatureAdoption(value) {
  if (!value || typeof value !== 'object') return value || '—'
  return Object.entries(value)
    .map(([name, amount]) => `${name} ${amount ?? '—'}${typeof amount === 'number' ? '%' : ''}`)
    .join(', ')
}

function titleCase(value) {
  if (!value) return ''
  return String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default App
