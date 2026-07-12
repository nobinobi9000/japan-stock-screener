import type { SupabaseClient } from '@supabase/supabase-js'

export type Plan = 'free' | 'basic' | 'premium'

/**
 * ログイン中ユーザーのプランを解決する。account_entitlements に行が
 * 無いユーザーは free 扱いとする（screener-snapshot Edge Function と同じ規約）。
 */
export async function resolvePlan(
  supabase: SupabaseClient,
  userId: string
): Promise<Plan> {
  const { data } = await supabase
    .from('account_entitlements')
    .select('plan')
    .eq('id', userId)
    .maybeSingle()

  const plan = data?.plan
  if (plan === 'basic' || plan === 'premium') return plan
  return 'free'
}

export function isPaidPlan(plan: Plan): boolean {
  return plan === 'basic' || plan === 'premium'
}
