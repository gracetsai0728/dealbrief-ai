export function ResultPanel({ result }) {
  if (!result) return null

  return (
    <section className="panel result-panel">
      <h2>AI-Generated Brief</h2>

      <div className="card">
        <h3>Customer Overview</h3>
        <p>{result.overview}</p>
      </div>

      <div className="card">
        <h3>Talking Points</h3>
        <ul>
          {result.talkingPoints.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h3>Suggested Questions</h3>
        <ul>
          {result.questions.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h3>Recommended Next Steps</h3>
        <p>{result.nextSteps}</p>
      </div>

      <div className="card">
        <h3>Potential Risks</h3>
        <p>{result.risk}</p>
      </div>
    </section>
  )
}
