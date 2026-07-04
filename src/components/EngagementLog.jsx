export function EngagementLog({ log }) {
  return (
    <section className="panel log-panel">
      <h2>Engagement Log</h2>
      {log.length === 0 ? (
        <p>No briefs generated yet. Click "Generate Brief" to start.</p>
      ) : (
        <ul>
          {log.map((item) => (
            <li key={item.id}>
              <strong>{item.customerName}</strong> / {item.meetingType} / {item.product} / {item.deliverable}
              <div className="log-meta">{item.createdAt}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
