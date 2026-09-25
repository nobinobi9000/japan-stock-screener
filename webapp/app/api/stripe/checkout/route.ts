import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { getStripe } from '@/lib/stripe'
import { resolvePlan, isPaidPlan } from '@/lib/entitlement'

export async function POST(request: Request) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user || !user.email) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  // 既に有償プランの場合は二重契約を防ぐ(プラン変更・解約はポータルから行う)
  if (isPaidPlan(await resolvePlan(supabase, user.id))) {
    return NextResponse.json({ error: 'already subscribed' }, { status: 409 })
  }

  // 過去に契約したことがあるユーザーはStripe顧客を再利用する(毎回新規顧客を作らない)
  const admin = createAdminClient()
  const { data: identity } = await admin
    .from('account_external_identities')
    .select('external_id')
    .eq('user_id', user.id)
    .eq('provider', 'stripe')
    .maybeSingle()

  const origin = new URL(request.url).origin

  const session = await getStripe().checkout.sessions.create({
    mode: 'subscription',
    locale: 'ja',
    line_items: [{ price: process.env.STRIPE_BASIC_PRICE_ID!, quantity: 1 }],
    client_reference_id: user.id,
    ...(identity?.external_id
      ? { customer: identity.external_id }
      : { customer_email: user.email }),
    success_url: `${origin}/?checkout=success`,
    cancel_url: `${origin}/?checkout=cancel`,
  })

  return NextResponse.json({ url: session.url })
}
