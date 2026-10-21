export async function fetchDashboard(signal) {
  const response = await fetch('/api/dashboard/summary', {
    signal,
    credentials: 'same-origin',
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const error = new Error(body.detail || `Dashboard request failed (${response.status})`)
    error.status = response.status
    throw error
  }
  return response.json()
}

export async function loginDashboard(token) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Login failed (${response.status})`)
  }
}

export function toDashboardReview(item) {
  const issue = item.issues?.[0]
  const severity = issue?.severity || 'info'
  const titleCase = (value) => value.charAt(0).toUpperCase() + value.slice(1)
  return {
    ...item,
    updated: new Date(item.updated_at).toLocaleString(),
    author: '—',
    initials: '—',
    branch: item.head_sha?.slice(0, 8) || 'head unavailable',
    status: issue ? 'Needs attention' : 'Reviewed',
    issueCount: item.issue_count,
    severity: titleCase(severity),
    file: issue?.path || item.changed_files?.[0] || 'No changed file recorded',
    line: issue?.line_number || '—',
    issue: issue?.message || 'No findings in this review',
    explanation: issue?.explanation || 'No explanation was recorded for this finding.',
    suggestedFix: issue?.fix_guidance || issue?.suggested_next_step || 'No fix guidance was recorded.',
    code: null,
    historicalExamples: issue?.historical_examples || [],
    history_message: issue?.history_message,
    findings: (item.issues || []).map((finding) => ({
      severity: titleCase(finding.severity || 'info'),
      path: finding.path,
      line: finding.line_number,
      message: finding.message,
      explanation: finding.explanation,
      risk: finding.risk,
      fix: finding.fix_guidance || finding.suggested_next_step,
      history: finding.historical_examples || [],
      historyMessage: finding.history_message,
    })),
    githubUrl: item.github_url,
  }
}
