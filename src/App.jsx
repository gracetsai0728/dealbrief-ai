import { useEffect, useState } from 'react'
import {
  createCustomer,
  createProduct,
  createSubscription,
  deleteCustomer,
  deleteSubscription,
  fetchCustomerDashboard,
  fetchCustomerTimeline,
  fetchCustomers,
  fetchCurrentUser,
  fetchProducts,
  fetchSubscriptions,
  generateBrief,
  login,
  logout,
  refreshIntelligence,
  register,
} from './api'
import { DELIVERABLES, MEETING_TYPES } from './constants'
import './App.css'

function App() {
  const [user, setUser] = useState(undefined)
  const [activeTab, setActiveTab] = useState('meeting')
  const [customers, setCustomers] = useState([])
  const [products, setProducts] = useState([])
  const [subscriptions, setSubscriptions] = useState([])
  const [timeline, setTimeline] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [selectedCustomerId, setSelectedCustomerId] = useState('')
  const [timelineCustomerId, setTimelineCustomerId] = useState('')
  const [intelligenceCustomerId, setIntelligenceCustomerId] = useState('')
  const [meetingType, setMeetingType] = useState(MEETING_TYPES[0])
  const [productId, setProductId] = useState('')
  const [deliverable, setDeliverable] = useState(DELIVERABLES[0])
  const [notes, setNotes] = useState('')
  const [brief, setBrief] = useState(null)
  const [busyAction, setBusyAction] = useState('')
  const [notice, setNotice] = useState(null)

  const loadData = async () => {
    const [customerData, productData, subscriptionData] =
      await Promise.all([
        fetchCustomers(),
        fetchProducts(),
        fetchSubscriptions(),
      ])
    setCustomers(customerData)
    setProducts(productData)
    setSubscriptions(subscriptionData)
    setSelectedCustomerId((current) =>
      customerData.some((item) => item.id === current) ? current : customerData[0]?.id || '',
    )
    setIntelligenceCustomerId((current) =>
      customerData.some((item) => item.id === current) ? current : customerData[0]?.id || '',
    )
    setTimelineCustomerId((current) =>
      customerData.some((item) => item.id === current) ? current : customerData[0]?.id || '',
    )
    setProductId((current) =>
      productData.some((item) => item.id === current) ? current : productData[0]?.id || '',
    )
  }

  useEffect(() => {
    fetchCurrentUser()
      .then(({ user: currentUser }) => setUser(currentUser))
      .catch(() => setUser(null))
  }, [])

  useEffect(() => {
    if (!user) return
    setActiveTab(user.role === 'admin' ? 'admin-add' : 'subscription')
    setBusyAction('initial-load')
    loadData()
      .catch((error) => setNotice({
        tab: user.role === 'admin' ? 'admin-add' : 'subscription',
        type: 'error',
        text: error.message,
      }))
      .finally(() => setBusyAction(''))
  }, [user])

  useEffect(() => {
    if (!user || user.role === 'admin' || !timelineCustomerId) {
      setTimeline(null)
      return
    }
    fetchCustomerTimeline(timelineCustomerId)
      .then(setTimeline)
      .catch((error) => setNotice({ tab: 'subscription', type: 'error', text: error.message }))
  }, [timelineCustomerId, user])

  useEffect(() => {
    if (!user || user.role === 'admin' || !intelligenceCustomerId) {
      setDashboard(null)
      return
    }
    fetchCustomerDashboard(intelligenceCustomerId)
      .then(setDashboard)
      .catch((error) => setNotice({ tab: 'intelligence', type: 'error', text: error.message }))
  }, [intelligenceCustomerId, user])

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
      'Meeting brief generated.',
      false,
    )
    if (result) setBrief(result)
  }

  const handleCopyBrief = async () => {
    if (!brief || !navigator.clipboard) return
    await navigator.clipboard.writeText(formatBriefForCopy(brief))
    setNotice({ tab: 'meeting', type: 'success', text: 'Brief copied to the clipboard.' })
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
      subscription: deleteSubscription,
    }
    await runAction(
      `delete-${kind}-${id}`,
      () => operations[kind](id),
      `${label} deleted.`,
    )
    if (intelligenceCustomerId) {
      fetchCustomerDashboard(intelligenceCustomerId).then(setDashboard).catch(() => setDashboard(null))
    }
    if (timelineCustomerId) {
      fetchCustomerTimeline(timelineCustomerId).then(setTimeline).catch(() => setTimeline(null))
    }
  }

  const handleLogout = async () => {
    await logout()
    setUser(null)
    setActiveTab('subscription')
    setCustomers([])
    setProducts([])
    setSubscriptions([])
    setTimeline(null)
  }

  if (user === undefined) {
    return <p className="auth-loading">Checking your session…</p>
  }

  if (!user) {
    return <AuthPage onAuthenticated={setUser} />
  }

  return (
    <div className="app">
      <header className="hero-section">
        <p className="eyebrow"><span className="hero-spark" aria-hidden="true">✦</span> AI Sales Meeting Brief Platform</p>
        <h1>DealBrief AI</h1>
        <p>Turn customer intelligence into sales-ready meeting briefs, email drafts, and meeting agendas.</p>
        <div className="account-bar">
          <span>{user.name} · {user.role === 'admin' ? 'Administrator' : 'User'}</span>
          <button className="btn-secondary" onClick={handleLogout}>Sign Out</button>
        </div>
      </header>

      <div className="tabs-container">
        <nav className="tabs-nav" aria-label="DealBrief AI sections">
          {user.role === 'admin' ? (
            <>
              <TabButton active={activeTab === 'admin-add'} onClick={() => setActiveTab('admin-add')}>
                Add Data
              </TabButton>
              <TabButton active={activeTab === 'admin-manage'} onClick={() => setActiveTab('admin-manage')}>
                Manage Data
              </TabButton>
            </>
          ) : (
            <>
              <TabButton active={activeTab === 'subscription'} onClick={() => setActiveTab('subscription')}>
                Subscription
              </TabButton>
              <TabButton active={activeTab === 'intelligence'} onClick={() => setActiveTab('intelligence')}>
                Intelligence
              </TabButton>
              <TabButton active={activeTab === 'meeting'} onClick={() => setActiveTab('meeting')}>
                Meeting Brief
              </TabButton>
            </>
          )}
        </nav>

        {notice?.tab === activeTab && (
          <div className={`api-notice ${notice.type}`}>{notice.text}</div>
        )}
        {busyAction === 'initial-load' ? (
          <p className="loading-state">Loading data from Flask and PostgreSQL…</p>
        ) : (
          <main className="tabs-content">
            {activeTab === 'subscription' && (
              <SubscriptionPage
                customers={customers}
                selectedCustomerId={timelineCustomerId}
                setSelectedCustomerId={setTimelineCustomerId}
                timeline={timeline}
              />
            )}

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

            {(activeTab === 'admin-add' || activeTab === 'admin-manage') && (
              <AdminDataManagementPage
                view={activeTab === 'admin-add' ? 'add' : 'manage'}
                customers={customers}
                products={products}
                subscriptions={subscriptions}
                busyAction={busyAction}
                onCreateCustomer={(payload) => runAction('create-customer', () => createCustomer(payload), 'Customer created.')}
                onCreateProduct={(payload) => runAction('create-product', () => createProduct(payload), 'Product created.')}
                onCreateSubscription={(payload) => runAction('create-subscription', () => createSubscription(payload), 'Subscription created.')}
                onDelete={handleDelete}
              />
            )}
          </main>
        )}
      </div>
    </div>
  )
}

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = mode === 'login'
        ? await login(email, password)
        : await register(name, email, password)
      onAuthenticated(result.user)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">AI Sales Meeting Brief Platform</p>
        <h1>DealBrief AI</h1>
        <p>{mode === 'login' ? 'Sign in to prepare customer meetings.' : 'Create your user account.'}</p>
        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && (
            <label className="field">
              Name
              <input value={name} maxLength="100" required onChange={(event) => setName(event.target.value)} />
            </label>
          )}
          <label className="field">
            Email
            <input type="email" value={email} maxLength="255" required onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="field">
            Password
            <input type="password" value={password} minLength="8" required onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error && <div className="api-notice error">{error}</div>}
          <button className="btn-primary" disabled={busy} type="submit">
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
        <button
          className="auth-switch"
          onClick={() => {
            setMode((current) => current === 'login' ? 'register' : 'login')
            setError('')
          }}
        >
          {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
        </button>
      </section>
    </main>
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
          onCopy={onCopy}
        />
      )}
    </section>
  )
}

const TIMELINE_COLORS = ['#0f766e', '#1d4ed8', '#b45309']
const ACTION_GROUPS = [
  ['crossSell', 'Cross-sell'],
  ['upsell', 'Upsell'],
  ['renewal', 'Renewal'],
  ['winback', 'Winback'],
]

function SubscriptionPage({ customers, selectedCustomerId, setSelectedCustomerId, timeline }) {
  const series = timeline?.series || []

  return (
    <section className="page-section timeline-page">
      <div className="section-heading">
        <h2>Subscription</h2>
        <p>Licensed seats for each product from the subscription start date through today.</p>
      </div>
      <div className="panel timeline-panel">
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
        <div className="subscription-summary-grid">
          {series.map((item, index) => (
            <article className="subscription-summary-card" key={item.subscriptionId}>
              <span
                className="series-dot"
                style={{ backgroundColor: TIMELINE_COLORS[index % TIMELINE_COLORS.length] }}
              />
              <div>
                <h3>{item.productName}</h3>
                <p>{formatDate(item.startDate)} – {item.endDate ? formatDate(item.endDate) : 'Ongoing'}</p>
                <p>{item.licensedSeats?.toLocaleString() ?? '—'} licensed seats</p>
              </div>
              <span className="status-pill">{titleCase(item.status)}</span>
            </article>
          ))}
        </div>
        {series.some((item) => item.seatPoints.length) ? (
          <SeatLineChart series={series} />
        ) : (
          <p className="empty-state">No licensed seat data is available.</p>
        )}
      </div>
    </section>
  )
}

function SeatLineChart({ series }) {
  const width = 960
  const height = 380
  const padding = { top: 28, right: 28, bottom: 52, left: 58 }
  const allPoints = series.flatMap((item) => item.seatPoints)
  const timestamps = allPoints.map((point) => new Date(`${point.date}T00:00:00`).getTime())
  const minTime = Math.min(...timestamps)
  const maxTime = Math.max(...timestamps)
  const timeSpan = Math.max(maxTime - minTime, 1)
  const plotWidth = width - padding.left - padding.right
  const plotHeight = height - padding.top - padding.bottom
  const x = (date) => padding.left + ((new Date(`${date}T00:00:00`).getTime() - minTime) / timeSpan) * plotWidth
  const maxSeats = Math.max(...allPoints.map((point) => Number(point.seats)), 1)
  const magnitude = 10 ** Math.floor(Math.log10(maxSeats))
  const normalizedMax = maxSeats / magnitude
  const niceFactor = normalizedMax <= 1 ? 1 : normalizedMax <= 2 ? 2 : normalizedMax <= 5 ? 5 : 10
  const yMaximum = niceFactor * magnitude
  const y = (value) => padding.top + (1 - Number(value) / yMaximum) * plotHeight
  const ticks = Array.from({ length: 5 }, (_, index) => (yMaximum / 4) * index)
  const dateTicks = [minTime, minTime + timeSpan / 2, maxTime]

  return (
    <div className="timeline-chart-wrap">
      <svg className="timeline-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Licensed seats by product over time">
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={y(tick)}
              y2={y(tick)}
              className="chart-grid-line"
            />
            <text x={padding.left - 12} y={y(tick) + 5} textAnchor="end" className="chart-axis-label">
              {tick.toLocaleString()}
            </text>
          </g>
        ))}
        {dateTicks.map((tick) => (
          <text
            key={tick}
            x={padding.left + ((tick - minTime) / timeSpan) * plotWidth}
            y={height - 18}
            textAnchor="middle"
            className="chart-axis-label"
          >
            {new Date(tick).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}
          </text>
        ))}
        {series.map((item, index) => {
          const color = TIMELINE_COLORS[index % TIMELINE_COLORS.length]
          const points = item.seatPoints.map((point) => `${x(point.date)},${y(point.seats)}`).join(' ')
          return (
            <g key={item.subscriptionId}>
              <polyline points={points} fill="none" stroke={color} strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />
              {item.seatPoints.map((point) => (
                <circle key={point.date} cx={x(point.date)} cy={y(point.seats)} r="4.5" fill={color}>
                  <title>{item.productName}: {point.seats.toLocaleString()} seats on {formatDate(point.date)}</title>
                </circle>
              ))}
            </g>
          )
        })}
      </svg>
    </div>
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

  return (
    <section className="page-section intelligence-page">
      <div className="section-heading">
        <h2>Customer Intelligence</h2>
      </div>

      <div className="panel intelligence-panel">
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
            {busy ? 'Searching and analyzing…' : 'Refresh Intelligence'}
          </button>
        </div>
      </div>

      <section className="intelligence-block">
        <IntelligenceSectionHeader
          title="Industry Dynamics"
          subtitle="Current market changes that may affect this customer."
        />
        <div className="intelligence-signal">
          <span>{customer?.industry || 'Industry unavailable'}</span>
        </div>
        <div className="intelligence-card-grid">
          {intelligence?.industryDynamics?.length ? intelligence.industryDynamics.map((item, index) => (
            <article className="insight-card" key={`${item.headline}-${index}`}>
              <h3>{item.headline}</h3>
              <p>{item.summary}</p>
              <strong>Customer impact</strong>
              <p>{item.impact}</p>
            </article>
          )) : <p className="empty-state">No industry analysis has been generated.</p>}
        </div>
      </section>

      <section className="intelligence-block">
        <IntelligenceSectionHeader
          title="Recent Company News"
          subtitle="Public sources when available; clearly labeled synthetic scenarios for demo accounts."
        />
        <div className="news-list">
          {intelligence?.companyNews?.length ? intelligence.companyNews.map((item, index) => (
            <article className="news-card" key={`${item.headline}-${index}`}>
              <div>
                <div className="news-meta">
                  <span>{item.publishedDate ? formatDate(item.publishedDate) : 'Recent'}</span>
                  {item.isMock && <span className="synthetic-news-badge">Synthetic demo</span>}
                </div>
                <h3>{item.headline}</h3>
                <p>{item.summary}</p>
              </div>
            </article>
          )) : <p className="empty-state">No reliable company-specific news was found.</p>}
        </div>
      </section>

      <section className="intelligence-block">
        <IntelligenceSectionHeader
          title="Recommended Next Steps"
          subtitle="Actions organized by commercial motion."
        />
        <div className="action-grid">
          {ACTION_GROUPS.map(([key, label]) => (
            <article className={`action-card action-${key}`} key={key}>
              <h3>{label}</h3>
              {(intelligence?.recommendedNextSteps?.[key] || []).map((action, index) => (
                <div className="action-item" key={`${action.action}-${index}`}>
                  <span className="priority-label">{titleCase(action.priority)}</span>
                  <strong>{action.action}</strong>
                  <p>{action.reason}</p>
                </div>
              ))}
              {!intelligence?.recommendedNextSteps?.[key]?.length && (
                <p className="empty-state">Refresh to generate a recommendation.</p>
              )}
            </article>
          ))}
        </div>
      </section>
    </section>
  )
}

function AdminDataManagementPage({
  view,
  customers,
  products,
  subscriptions,
  busyAction,
  onCreateCustomer,
  onCreateProduct,
  onCreateSubscription,
  onDelete,
}) {
  return (
    <section className="page-section data-management-page">
      <div className="section-heading">
        <h2>Admin Data Management</h2>
      </div>
      <div className="overview-grid">
        <MetricCard label="Total Customers" value={customers.length} />
        <MetricCard label="Products" value={products.length} />
        <MetricCard label="Subscriptions" value={subscriptions.length} />
      </div>

      {view === 'add' ? (
        <div className="admin-form-grid">
          <CustomerCreateForm busy={busyAction === 'create-customer'} onSubmit={onCreateCustomer} />
          <ProductCreateForm busy={busyAction === 'create-product'} onSubmit={onCreateProduct} />
          <SubscriptionCreateForm
            customers={customers}
            products={products}
            busy={busyAction === 'create-subscription'}
            onSubmit={onCreateSubscription}
          />
        </div>
      ) : (
        <div className="admin-manage-panels">
          <DataTable tone="blue" title="Manage Customers" columns={['Customer Name', 'Industry', 'Status', 'Action']}>
            {customers.map((customer) => (
              <tr key={customer.id}>
                <td>{customer.name}</td>
                <td>{customer.industry || '—'}</td>
                <td><span className="status-pill">{titleCase(customer.status)}</span></td>
                <td>
                  <button className="table-action" onClick={() => onDelete('customer', customer.id, customer.name)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </DataTable>

          <DataTable tone="blue" title="Manage Products" columns={['Product Name', 'Description', 'Status']}>
            {products.map((product) => (
              <tr key={product.id}>
                <td>{product.name}</td>
                <td>{product.description || '—'}</td>
                <td><span className="status-pill">{titleCase(product.status)}</span></td>
              </tr>
            ))}
          </DataTable>

          <DataTable tone="green" title="Manage Subscriptions" columns={['Customer', 'Product', 'Subscription Start', 'Subscription End', 'Status', 'Licensed Seats', 'Action']}>
            {subscriptions.map((record) => (
              <tr key={record.id}>
                <td>{record.customerName || record.customerId}</td>
                <td>{record.productName}</td>
                <td>{formatDate(record.subscriptionStartDate)}</td>
                <td>{formatDate(record.subscriptionEndDate)}</td>
                <td><span className="status-pill">{titleCase(record.subscriptionStatus)}</span></td>
                <td>{record.licensedSeats ?? '—'}</td>
                <td>
                  <button className="table-action" onClick={() => onDelete('subscription', record.id, `${record.customerName} subscription`)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </DataTable>
        </div>
      )}

    </section>
  )
}

function CustomerCreateForm({ busy, onSubmit }) {
  const [form, setForm] = useState({ name: '', industry: '' })
  const update = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }))
  const submit = async (event) => {
    event.preventDefault()
    const result = await onSubmit(form)
    if (result) setForm({ name: '', industry: '' })
  }
  return (
    <form className="panel admin-entry-form" onSubmit={submit}>
      <h3>Add Customer</h3>
      <label className="field">Name<input required value={form.name} onChange={update('name')} /></label>
      <label className="field">Industry<input value={form.industry} onChange={update('industry')} /></label>
      <button className="btn-primary" disabled={busy}>{busy ? 'Adding…' : 'Add Customer'}</button>
    </form>
  )
}

function ProductCreateForm({ busy, onSubmit }) {
  const [form, setForm] = useState({ name: '', description: '' })
  const submit = async (event) => {
    event.preventDefault()
    const result = await onSubmit(form)
    if (result) setForm({ name: '', description: '' })
  }
  return (
    <form className="panel admin-entry-form" onSubmit={submit}>
      <h3>Add Product</h3>
      <label className="field">Name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
      <label className="field field-grow">Description<textarea rows="5" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <button className="btn-primary" disabled={busy}>{busy ? 'Adding…' : 'Add Product'}</button>
    </form>
  )
}

function SubscriptionCreateForm({ customers, products, busy, onSubmit }) {
  const [form, setForm] = useState({
    customerId: '',
    productId: '',
    subscriptionStartDate: '',
    subscriptionEndDate: '',
    subscriptionStatus: 'active',
    licensedSeats: '',
  })
  const value = (field, fallback) => form[field] || fallback
  const update = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }))
  const submit = async (event) => {
    event.preventDefault()
    const result = await onSubmit({
      ...form,
      customerId: value('customerId', customers[0]?.id),
      productId: value('productId', products[0]?.id),
    })
    if (result) setForm({
      customerId: '',
      productId: '',
      subscriptionStartDate: '',
      subscriptionEndDate: '',
      subscriptionStatus: 'active',
      licensedSeats: '',
    })
  }
  return (
    <form className="panel admin-entry-form" onSubmit={submit}>
      <h3>Add Subscription</h3>
      <SelectField label="Customer" value={value('customerId', customers[0]?.id || '')} onChange={(next) => setForm({ ...form, customerId: next })}>
        {customers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
      </SelectField>
      <SelectField label="Product" value={value('productId', products[0]?.id || '')} onChange={(next) => setForm({ ...form, productId: next })}>
        {products.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
      </SelectField>
      <label className="field">Subscription Start<input type="date" required value={form.subscriptionStartDate} onChange={update('subscriptionStartDate')} /></label>
      <label className="field">Subscription End<input type="date" value={form.subscriptionEndDate} onChange={update('subscriptionEndDate')} /></label>
      <SelectField label="Status" value={form.subscriptionStatus} onChange={(next) => setForm({ ...form, subscriptionStatus: next })}>
        <option value="active">Active</option>
        <option value="expired">Expired</option>
        <option value="canceled">Canceled</option>
      </SelectField>
      <label className="field">Licensed Seats<input type="number" min="0" value={form.licensedSeats} onChange={update('licensedSeats')} /></label>
      <button className="btn-primary" disabled={busy || !customers.length || !products.length}>{busy ? 'Adding…' : 'Add Subscription'}</button>
    </form>
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

function BriefResult({ brief, onCopy }) {
  const deliverableType = brief.deliverableType || brief.deliverable?.toLowerCase().replaceAll(' ', '_')
  return (
    <section className="result-panel">
      <div className="result-heading">
        <div>
          <span>{brief.meetingType} · {brief.product}</span>
          <h2>{brief.title}</h2>
          <p>{brief.summary}</p>
        </div>
      </div>

      {deliverableType === 'email_draft' ? (
        <EmailDraftResult brief={brief} />
      ) : deliverableType === 'meeting_agenda' ? (
        <MeetingAgendaResult brief={brief} />
      ) : (
        <CallBriefResult brief={brief} />
      )}
      <div className="result-actions">
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

function titleCase(value) {
  if (!value) return ''
  return String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default App
