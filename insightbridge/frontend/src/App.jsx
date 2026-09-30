import { useState } from 'react'

const samples = [
  'Which California customers use premium plans?',
  'Show revenue by quarter in 2023.',
  'Which customers have high or critical churn risk?',
  'Show open sales opportunities.',
]

function formatValue(value, column) {
  if (value === null || value === '') return '—'
  if (typeof value === 'number' && /revenue|mrr|spend|cost/i.test(column)) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
  }
  if (typeof value === 'number') return new Intl.NumberFormat('en-US').format(value)
  return String(value).replaceAll('_', ' ')
}

function App() {
  const [question, setQuestion] = useState(samples[0])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function ask(event) {
    event?.preventDefault()
    if (!question.trim() || loading) return
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'The request failed.')
      setResult(data)
    } catch (requestError) {
      setError(requestError.message === 'Failed to fetch'
        ? 'Could not reach the API. Make sure Flask is running on port 5000.'
        : requestError.message)
    } finally {
      setLoading(false)
    }
  }

  function useSample(sample) {
    setQuestion(sample)
    setError('')
  }

  return (
    <main>
      <section className="hero">
        <div className="brand">IB</div>
        <p className="eyebrow">Natural-language business intelligence</p>
        <h1>InsightBridge</h1>
        <p className="subtitle">Ask your business data in plain English</p>

        <form onSubmit={ask} className="question-form">
          <label htmlFor="question">What would you like to know?</label>
          <div className="input-row">
            <input
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about revenue, customers, subscriptions, or sales…"
              maxLength={500}
            />
            <button disabled={loading || !question.trim()}>
              {loading ? 'Asking…' : 'Ask'}
            </button>
          </div>
        </form>

        <div className="samples" aria-label="Sample questions">
          {samples.map((sample) => (
            <button type="button" key={sample} onClick={() => useSample(sample)}>{sample}</button>
          ))}
        </div>
      </section>

      {error && <section className="message error"><strong>Something went wrong</strong><p>{error}</p></section>}

      {result && (
        <section className="result-card">
          <div className={result.clarification ? 'summary clarification' : 'summary'}>
            <span>{result.clarification ? '?' : '✓'}</span>
            <div><small>{result.clarification ? 'Clarification needed' : 'Answer'}</small><h2>{result.summary}</h2></div>
          </div>

          {!result.clarification && result.rows.length === 0 && (
            <div className="empty">No rows matched the detected filters. Try broadening the question.</div>
          )}

          {result.rows.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead><tr>{result.columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead>
                <tbody>
                  {result.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>{row.map((value, index) => <td key={index}>{formatValue(value, result.columns[index])}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <details>
            <summary>How did I answer this?</summary>
            <dl>
              <div><dt>Intent</dt><dd>{result.explanation.intent.replaceAll('_', ' ')}</dd></div>
              <div><dt>Tables</dt><dd>{result.explanation.tables.join(', ') || 'None'}</dd></div>
              <div><dt>Filters</dt><dd>{result.explanation.filters.join(', ') || 'None'}</dd></div>
              <div><dt>Parser</dt><dd>{result.explanation.parser}</dd></div>
            </dl>
          </details>

          {result.sql && <details><summary>Generated SQL</summary><pre>{result.sql}</pre></details>}
        </section>
      )}
    </main>
  )
}

export default App
