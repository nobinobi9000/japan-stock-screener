import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { resolvePlan, isPaidPlan } from '@/lib/entitlement'
import AnalysisTable from './AnalysisTable'

export const dynamic = 'force-dynamic'

export default async function AnalysisPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  // '/analysis' はproxy.tsで未ログイン時にリダイレクト済みのため、ここでは常にuserが存在する
  const plan = user ? await resolvePlan(supabase, user.id) : 'free'

  return (
    <main className="relative z-10 min-h-screen px-4 py-10">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="text-sm text-[var(--muted)] hover:text-[var(--green)]">
            ← トップへ戻る
          </Link>
        </div>

        <h1 className="text-2xl font-bold text-[var(--head)] mb-2">全銘柄分析</h1>
        <p className="text-sm text-[var(--muted)] mb-8">
          スクリーナーバッチが日次で判定した条件成立の事実表示です。売買の推奨・示唆は含みません。
        </p>

        {isPaidPlan(plan) ? (
          <AnalysisTable />
        ) : (
          <div className="bg-[var(--panel)] border border-[var(--border2)] rounded-xl p-8 text-center">
            <p className="text-[var(--head)] font-semibold mb-2">
              全銘柄分析はbasic・premiumプランでご利用いただけます
            </p>
            <p className="text-sm text-[var(--muted)]">
              現在のプラン: free（無料枠は厳選3銘柄＋市場サマリーのみ表示）
            </p>
          </div>
        )}
      </div>
    </main>
  )
}
