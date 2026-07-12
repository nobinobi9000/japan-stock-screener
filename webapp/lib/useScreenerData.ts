'use client'

import { useState, useEffect } from 'react'

// screener.nobi-labo.comへのCNAME設定により、GitHub PagesのURLへ直接fetch()すると
// 301リダイレクト(CORSヘッダ無し)で失敗するため、同一オリジンのAPIルート経由で取得する
// (webapp/app/api/free-latest/route.ts がraw.githubusercontent.com経由でサーバー側取得)
const SCREENER_URL = '/api/free-latest'
const CACHE_KEY = 'screener_latest'
const CACHE_DATE_KEY = 'screener_latest_date'

export type Top3Stock = {
  code: string
  name: string
  score: number
  price: number | null
  risk_tag: string
  sector: string
  pattern: string
}

export type SectorHeatmapEntry = {
  name: string
  avg_score: number
  stock_count: number
}

export type ScreenerFreeData = {
  date: string
  top3: Top3Stock[]
  sector_heatmap: SectorHeatmapEntry[]
  market_summary?: Record<string, unknown>
}

/**
 * 日本株スクリーナーの latest.json（無料枠: 厳選3銘柄＋サマリー）を取得するフック。
 * 当日キャッシュ（localStorage）を使い、1日1回だけ実際に fetch する。
 */
export function useScreenerData() {
  const [data, setData] = useState<ScreenerFreeData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      const cachedDate = localStorage.getItem(CACHE_DATE_KEY)
      const today = new Date().toISOString().slice(0, 10)

      if (cachedDate === today) {
        const cachedRaw = localStorage.getItem(CACHE_KEY)
        if (cachedRaw) {
          try {
            setData(JSON.parse(cachedRaw))
            setLoading(false)
            return
          } catch {
            // キャッシュ破損 → 再フェッチ
          }
        }
      }

      try {
        const res = await fetch(SCREENER_URL)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json = await res.json()
        localStorage.setItem(CACHE_KEY, JSON.stringify(json))
        localStorage.setItem(CACHE_DATE_KEY, today)
        setData(json)
      } catch {
        const staleRaw = localStorage.getItem(CACHE_KEY)
        if (staleRaw) {
          try {
            setData(JSON.parse(staleRaw))
          } catch {
            setError('データの取得に失敗しました')
          }
        } else {
          setError('データの取得に失敗しました')
        }
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  return { data, loading, error }
}
