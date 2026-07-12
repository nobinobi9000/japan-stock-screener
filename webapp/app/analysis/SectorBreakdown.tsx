'use client'

import { useMemo } from 'react'
import type { StockSnapshot } from './AnalysisTable'

export default function SectorBreakdown({ stocks }: { stocks: StockSnapshot[] }) {
  const rows = useMemo(() => {
    const bySector = new Map<string, { count: number; scoreSum: number }>()
    for (const s of stocks) {
      const key = s.sector ?? '不明'
      const entry = bySector.get(key) ?? { count: 0, scoreSum: 0 }
      entry.count += 1
      entry.scoreSum += s.total_score ?? 0
      bySector.set(key, entry)
    }
    return Array.from(bySector.entries())
      .map(([name, { count, scoreSum }]) => ({
        name,
        count,
        avgScore: count > 0 ? scoreSum / count : 0,
      }))
      .sort((a, b) => b.avgScore - a.avgScore)
  }, [stocks])

  if (rows.length === 0) return null

  const maxScore = Math.max(...rows.map((r) => r.avgScore), 1)

  return (
    <div className="bg-[var(--panel)] border border-[var(--border2)] rounded-xl p-4">
      <h2 className="text-sm font-semibold text-[var(--head)] mb-3">セクター別平均スコア</h2>
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.name} className="flex items-center gap-3 text-xs">
            <span className="w-32 shrink-0 text-[var(--text)] truncate">{r.name}</span>
            <div className="flex-1 h-2 bg-[var(--panel2)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--green)] rounded-full"
                style={{ width: `${(r.avgScore / maxScore) * 100}%` }}
              />
            </div>
            <span className="w-16 shrink-0 text-right text-[var(--green2)]">
              {r.avgScore.toFixed(1)}
            </span>
            <span className="w-14 shrink-0 text-right text-[var(--muted)]">{r.count}銘柄</span>
          </div>
        ))}
      </div>
    </div>
  )
}
