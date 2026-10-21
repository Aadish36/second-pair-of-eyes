import { describe, expect, it, vi } from 'vitest'
import { fetchDashboard, toDashboardReview } from './api.js'

describe('dashboard API mapping', () => {
  it('maps persisted review fields without inventing findings', () => {
    const review = toDashboardReview({
      id: 'review-1', number: 7, title: 'Fix bug', repository: 'org/repo',
      head_sha: 'abc123def', updated_at: '2026-10-20T10:00:00Z', issue_count: 1,
      issues: [{ severity: 'high', path: 'src/main.py', line_number: 12,
        message: 'Undefined name', suggested_next_step: 'Define it',
        historical_examples: [], history_message: 'No history.' }],
      changed_files: ['src/main.py'], github_url: 'https://github.com/org/repo/pull/7',
    })
    expect(review.issue).toBe('Undefined name')
    expect(review.file).toBe('src/main.py')
    expect(review.line).toBe(12)
    expect(review.suggestedFix).toBe('Define it')
    expect(review.author).toBe('—')
    expect(review.githubUrl).toContain('/pull/7')
    expect(review.findings).toHaveLength(1)
    expect(review.findings[0].risk).toBeUndefined()
  })

  it('fetches the backend summary and surfaces server errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ items: [], total: 0 }) }))
    await expect(fetchDashboard()).resolves.toMatchObject({ total: 0 })
    expect(fetch).toHaveBeenCalledWith('/api/dashboard/summary', expect.objectContaining({ credentials: 'same-origin' }))

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: 'Database unavailable' }) }))
    await expect(fetchDashboard()).rejects.toThrow('Database unavailable')
    vi.unstubAllGlobals()
  })
})
