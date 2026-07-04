export function ResultPanel({ result, onLogEngagement, isLogView, onClose }) {
  if (!result) return null

  const renderCall = () => (
    <>
      <div className="card">
        <h3>Customer Overview</h3>
        <p>{result.overview}</p>
      </div>
      <div className="card">
        <h3>Call Objective</h3>
        <p>{result.callObjective}</p>
      </div>
      <div className="card">
        <h3>Talking Points</h3>
        <ul>{result.talkingPoints.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </div>
      <div className="card">
        <h3>Suggested Questions</h3>
        <ul>{result.questions.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </div>
      <div className="card">
        <h3>Closing and Next Steps</h3>
        <p>{result.nextSteps}</p>
      </div>
      <div className="card">
        <h3>Potential Risk</h3>
        <p>{result.risk}</p>
      </div>
    </>
  )

  const renderEmail = () => (
    <div className="email-preview">
      <div className="email-field"><strong>To:</strong> {result.email.to}</div>
      <div className="email-field"><strong>Subject:</strong> {result.email.subject}</div>
      <div className="email-body">
        <p>{result.email.greeting}</p>
        {result.email.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}
        <p>{result.email.callToAction}</p>
        <p className="email-signoff">{result.email.signOff}</p>
      </div>
    </div>
  )

  const renderAgenda = () => (
    <>
      <div className="agenda-summary">
        <div><span>Objective</span><p>{result.objective}</p></div>
        <div><span>Duration</span><p>{result.duration}</p></div>
      </div>
      <div className="agenda-list">
        {result.agendaItems.map((item, index) => (
          <div className="agenda-item" key={index}>
            <span className="agenda-time">{item.time}</span>
            <div><h3>{item.title}</h3><p>{item.detail}</p></div>
          </div>
        ))}
      </div>
      <div className="card">
        <h3>Preparation</h3>
        <ul>{result.preparation.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </div>
      <div className="card">
        <h3>Desired Outcome</h3>
        <p>{result.desiredOutcome}</p>
      </div>
    </>
  )

  return (
    <section className="panel result-panel">
      <div className="result-header">
        <div>
          <span className="deliverable-label">{result.deliverable}</span>
          <h2>{result.deliverable === 'Email' ? 'Customer Email' : result.deliverable}</h2>
        </div>
        {isLogView && (
          <button className="btn-close" onClick={onClose} title="Close">
            ✕
          </button>
        )}
      </div>

      {result.deliverable === 'Email' && renderEmail()}
      {result.deliverable === 'Meeting Agenda' && renderAgenda()}
      {result.deliverable === 'Call' && renderCall()}

      {onLogEngagement && (
        <button className="btn btn-primary" onClick={onLogEngagement}>
          Log Engagement
        </button>
      )}
    </section>
  )
}
