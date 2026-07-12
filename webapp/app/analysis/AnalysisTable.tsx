'use client'

import { useEffect, useMemo, useState } from 'react'
import SectorBreakdown from './SectorBreakdown'

export type StockSnapshot = {
  id: string
  snapshot_date: string
  code: string
  name: string
  sector: string | null
  close_price: number | null
  fetch_success: boolean
  ma_trend: boolean | null
  golden_cross: boolean | null
  bottom_cross: boolean | null
  bb_signal: boolean | null
  obv_trend: boolean | null
  ichimoku_cloud: boolean | null
  ichimoku_sanryo: boolean | null
  volume_surge: boolean | null
  pbr_value: boolean | null
  total_score: number | null
  jvqm_score: number | null
  momentum_12m: number | null
  near_52w_high: boolean | null
  dead_cross: boolean | null
  ma200_breakdown: boolean | null
  ichimoku_bearish: boolean | null
  bb_lower_break: boolean | null
  obv_downtrend: boolean | null
  volume_surge_down: boolean | null
}

type SnapshotMeta = {
  snapshot_date: string
  total_scanned: number
  success_count: number
  success_rate: number
  is_incomplete: boolean
}

type SnapshotResponse = {
  snapshot: SnapshotMeta
  stocks: StockSnapshot[]
}

type SortKey = 'code' | 'total_score' | 'jvqm_score' | 'momentum_12m'

const BUY_SIGNAL_COLUMNS: { key: keyof StockSnapshot; label: string }[] = [
  { key: 'golden_cross', label: 'GC' },
  { key: 'ma_trend', label: 'MA200上向き' },
  { key: 'bottom_cross', label: '底値クロス' },
  { key: 'bb_signal', label: 'BB' },
  { key: 'obv_trend', label: 'OBV上昇' },
  { key: 'ichimoku_cloud', label: '雲上抜け' },
  { key: 'ichimoku_sanryo', label: '三役好転' },
  { key: 'volume_surge', label: '出来高急増' },
  { key: 'pbr_value', label: 'PBR割安' },
  { key: 'near_52w_high', label: '52週高値近辺' },
]

const SELL_SIGNAL_COLUMNS: { key: keyof StockSnapshot; label: string }[] = [
  { key: 'dead_cross', label: 'DC' },
  { key: 'ma200_breakdown', label: 'MA200割れ' },
  { key: 'ichimoku_bearish', label: '三役逆転' },
  { key: 'bb_lower_break', label: 'BB下限割れ' },
  { key: 'obv_downtrend', label: 'OBV下降' },
  { key: 'volume_surge_down', label: '出来高急増(下落)' },
]

export default function AnalysisTable() {
  const [data, setData] = useState<SnapshotResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const [query, setQuery] = useState('')
  const [sector, setSector] = useState('すべて')
  const [sortKey, setSortKey] = useState<SortKey>('total_score')
  const [sortDesc, setSortDesc] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/snapshot')
        if (res.status === 404) {
          setNotFound(true)
          setLoading(false)
          return
        }
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        const json = await res.json()
        setData(json)
      } catch {
        setError('データの取得に失敗しました')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const sectors = useMemo(() => {
    if (!data) return []
    const set = new Set(data.stocks.map((s) => s.sector).filter((s): s is string => !!s))
    return Array.from(set).sort()
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    let rows = data.stocks
    if (sector !== 'すべて') {
      rows = rows.filter((s) => s.sector === sector)
    }
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      rows = rows.filter(
        (s) => s.code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
      )
    }
    const sorted = [...rows].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av === null && bv === null) return 0
      if (av === null) return 1
      if (bv === null) return -1
      if (typeof av === 'number' && typeof bv === 'number') {
        return sortDesc ? bv - av : av - bv
      }
      return sortDesc ? String(bv).localeCompare(String(av)) : String(av).localeCompare(String(bv))
    })
    return sorted
  }, [data, sector, query, sortKey, sortDesc])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDesc((d) => !d)
    } else {
      setSortKey(key)
      setSortDesc(true)
    }
  }

  if (loading) {
    return <p className="text-[var(--muted)] text-sm">読み込み中...</p>
  }

  if (error) {
    return <p className="text-red-400 text-sm">{error}</p>
  }

  if (notFound || !data) {
    return (
      <div className="bg-[var(--panel)] border border-[var(--border2)] rounded-xl p-8 text-center">
        <p className="text-[var(--head)] font-semibold">本日は配信なし/データ取得不可</p>
        <p className="text-sm text-[var(--muted)] mt-2">
          スナップショットがまだ生成されていません。バッチの完了後に表示されます。
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]">
        <span>
          基準日: <span className="text-[var(--text)]">{data.snapshot.snapshot_date}</span>
        </span>
        <span>
          取得成功: {data.snapshot.success_count}/{data.snapshot.total_scanned}銘柄（
          {(data.snapshot.success_rate * 100).toFixed(1)}%）
        </span>
        {data.snapshot.is_incomplete && (
          <span className="text-[var(--amber)]">
            ※本日のスナップショットは一部データが欠損しています
          </span>
        )}
      </div>

      <SectorBreakdown stocks={data.stocks} />

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="コード・銘柄名で検索"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="px-3 py-2 rounded-lg border border-[var(--border2)] bg-[var(--bg)] text-sm text-[var(--head)] focus:outline-none focus:ring-2 focus:ring-[var(--green)]"
        />
        <select
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          className="px-3 py-2 rounded-lg border border-[var(--border2)] bg-[var(--bg)] text-sm text-[var(--head)] focus:outline-none focus:ring-2 focus:ring-[var(--green)]"
        >
          <option>すべて</option>
          {sectors.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <span className="text-xs text-[var(--muted)]">{filtered.length}件表示</span>
      </div>

      <div className="overflow-x-auto border border-[var(--border2)] rounded-xl">
        <table className="min-w-full text-xs">
          <thead className="bg-[var(--panel2)] text-[var(--muted)]">
            <tr>
              <Th onClick={() => toggleSort('code')} active={sortKey === 'code'} desc={sortDesc}>
                コード
              </Th>
              <th className="px-3 py-2 text-left">銘柄名</th>
              <th className="px-3 py-2 text-left">セクター</th>
              <th className="px-3 py-2 text-right">株価</th>
              <Th onClick={() => toggleSort('total_score')} active={sortKey === 'total_score'} desc={sortDesc}>
                総合スコア
              </Th>
              <Th onClick={() => toggleSort('jvqm_score')} active={sortKey === 'jvqm_score'} desc={sortDesc}>
                JVQM
              </Th>
              <Th
                onClick={() => toggleSort('momentum_12m')}
                active={sortKey === 'momentum_12m'}
                desc={sortDesc}
              >
                12ヶ月モメンタム
              </Th>
              {BUY_SIGNAL_COLUMNS.map((c) => (
                <th key={String(c.key)} className="px-2 py-2 text-center whitespace-nowrap">
                  {c.label}
                </th>
              ))}
              {SELL_SIGNAL_COLUMNS.map((c) => (
                <th key={String(c.key)} className="px-2 py-2 text-center whitespace-nowrap">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.id} className="border-t border-[var(--border2)] hover:bg-[var(--panel2)]">
                <td className="px-3 py-2 font-[family-name:var(--mono)] text-[var(--head)]">
                  {s.code}
                </td>
                <td className="px-3 py-2 text-[var(--text)]">{s.name}</td>
                <td className="px-3 py-2 text-[var(--muted)]">{s.sector ?? '—'}</td>
                <td className="px-3 py-2 text-right text-[var(--text)]">
                  {s.close_price !== null ? s.close_price.toLocaleString() : '—'}
                </td>
                <td className="px-3 py-2 text-right text-[var(--green2)]">
                  {s.total_score !== null ? s.total_score.toFixed(1) : '—'}
                </td>
                <td className="px-3 py-2 text-right text-[var(--text)]">
                  {s.jvqm_score !== null ? s.jvqm_score.toFixed(1) : '—'}
                </td>
                <td className="px-3 py-2 text-right text-[var(--text)]">
                  {s.momentum_12m !== null ? `${(s.momentum_12m * 100).toFixed(1)}%` : '—'}
                </td>
                {BUY_SIGNAL_COLUMNS.map((c) => (
                  <td key={String(c.key)} className="px-2 py-2 text-center">
                    {s[c.key] ? <span className="text-[var(--green)]">●</span> : ''}
                  </td>
                ))}
                {SELL_SIGNAL_COLUMNS.map((c) => (
                  <td key={String(c.key)} className="px-2 py-2 text-center">
                    {s[c.key] ? <span className="text-[var(--red)]">●</span> : ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Th({
  children,
  onClick,
  active,
  desc,
}: {
  children: React.ReactNode
  onClick: () => void
  active: boolean
  desc: boolean
}) {
  return (
    <th
      onClick={onClick}
      className="px-3 py-2 text-left cursor-pointer select-none hover:text-[var(--text)] whitespace-nowrap"
    >
      {children}
      {active && <span className="ml-1">{desc ? '▼' : '▲'}</span>}
    </th>
  )
}
