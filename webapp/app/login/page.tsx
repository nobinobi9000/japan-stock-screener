'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  const router = useRouter()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setInfo('')
    setLoading(true)

    const supabase = createClient()

    if (mode === 'login') {
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) {
        setError(error.message)
        setLoading(false)
        return
      }
      router.push('/')
      router.refresh()
    } else {
      const { error } = await supabase.auth.signUp({ email, password })
      if (error) {
        setError(error.message)
        setLoading(false)
        return
      }
      setInfo('確認メールを送信しました。メール内のリンクから登録を完了してください。')
      setLoading(false)
    }
  }

  return (
    <main className="relative z-10 min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link href="/" className="text-2xl font-bold text-[var(--green)] font-[family-name:var(--mono)]">
            日本株スクリーナー
          </Link>
          <p className="text-[var(--muted)] text-sm mt-2">
            Kabu Note・kabu-signalと共通のアカウントでログインできます
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[var(--panel)] border border-[var(--border2)] rounded-xl p-6 space-y-4"
        >
          <h2 className="text-lg font-semibold text-[var(--head)]">
            {mode === 'login' ? 'ログイン' : '新規登録'}
          </h2>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/50 rounded p-2">{error}</p>
          )}
          {info && (
            <p className="text-sm text-[var(--green2)] bg-emerald-950/50 rounded p-2">{info}</p>
          )}

          <div>
            <label className="block text-sm font-medium mb-1 text-[var(--text)]">
              メールアドレス
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border2)] bg-[var(--bg)] text-sm text-[var(--head)] focus:outline-none focus:ring-2 focus:ring-[var(--green)]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-[var(--text)]">
              パスワード
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border2)] bg-[var(--bg)] text-sm text-[var(--head)] focus:outline-none focus:ring-2 focus:ring-[var(--green)]"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-[var(--green)] hover:opacity-90 text-[#04080f] font-semibold rounded-lg disabled:opacity-50 transition"
          >
            {loading ? '処理中...' : mode === 'login' ? 'ログイン' : '登録する'}
          </button>

          <p className="text-center text-sm text-[var(--muted)]">
            {mode === 'login' ? (
              <>
                アカウントをお持ちでない方は{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('signup')
                    setError('')
                    setInfo('')
                  }}
                  className="text-[var(--green)] hover:underline"
                >
                  新規登録
                </button>
              </>
            ) : (
              <>
                既にアカウントをお持ちの方は{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('login')
                    setError('')
                    setInfo('')
                  }}
                  className="text-[var(--green)] hover:underline"
                >
                  ログイン
                </button>
              </>
            )}
          </p>
        </form>

        <p className="text-center mt-6">
          <Link href="/" className="text-xs text-[var(--muted)] hover:text-[var(--green)]">
            ← トップへ戻る
          </Link>
        </p>
      </div>
    </main>
  )
}
