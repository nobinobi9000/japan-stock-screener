import { NextResponse } from 'next/server'
import Stripe from 'stripe'
import { getStripe } from '@/lib/stripe'
import { createAdminClient } from '@/lib/supabase/admin'

export const dynamic = 'force-dynamic'

// この状態になったらプランを free に戻す。past_due は Stripe が支払いを再試行中のため
// 猶予として現プランを維持し、最終的に canceled/unpaid になった時点で free にする。
const ENDED_STATUSES = new Set<string>(['canceled', 'unpaid', 'incomplete_expired'])
const ACTIVE_STATUSES = new Set<string>(['active', 'trialing', 'past_due'])

function customerIdOf(customer: string | Stripe.Customer | Stripe.DeletedCustomer | null): string | null {
  if (!customer) return null
  return typeof customer === 'string' ? customer : customer.id
}

// Stripeからの直接呼び出し(ユーザーセッション無し)。署名検証で真正性を担保するため
// proxy.ts の PUBLIC_PATHS で未ログイン扱いを許可している。
//
// DB書き込みに失敗した場合は必ず500を返す。200を返すとStripeが再送せず、
// 「課金されたのにプランが反映されない」状態が黙って残るため(原則5)。
export async function POST(request: Request) {
  const body = await request.text()
  const signature = request.headers.get('stripe-signature')

  if (!signature) {
    return NextResponse.json({ error: 'missing signature' }, { status: 400 })
  }

  let event: Stripe.Event
  try {
    event = getStripe().webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err) {
    return NextResponse.json({ error: `invalid signature: ${err}` }, { status: 400 })
  }

  const admin = createAdminClient()

  async function setPlanByCustomer(customerId: string, plan: 'free' | 'basic') {
    const { data: identity, error: findErr } = await admin
      .from('account_external_identities')
      .select('user_id')
      .eq('provider', 'stripe')
      .eq('external_id', customerId)
      .maybeSingle()
    if (findErr) throw findErr
    if (!identity?.user_id) return // 未紐付けの顧客(本サービス経由でない契約等)は対象外

    const { error } = await admin
      .from('account_entitlements')
      .upsert({ id: identity.user_id, plan, plan_source: 'stripe', updated_at: new Date().toISOString() })
    if (error) throw error
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        const userId = session.client_reference_id
        const customerId = customerIdOf(session.customer)
        if (!userId || !customerId) break

        const { error: identityErr } = await admin
          .from('account_external_identities')
          .upsert(
            { user_id: userId, provider: 'stripe', external_id: customerId },
            { onConflict: 'user_id,provider' }
          )
        if (identityErr) throw identityErr

        const { error: planErr } = await admin
          .from('account_entitlements')
          .upsert({ id: userId, plan: 'basic', plan_source: 'stripe', updated_at: new Date().toISOString() })
        if (planErr) throw planErr
        break
      }

      case 'customer.subscription.updated':
      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription
        const customerId = customerIdOf(subscription.customer)
        if (!customerId) break

        const ended = event.type === 'customer.subscription.deleted' || ENDED_STATUSES.has(subscription.status)
        if (ended) {
          await setPlanByCustomer(customerId, 'free')
        } else if (ACTIVE_STATUSES.has(subscription.status)) {
          await setPlanByCustomer(customerId, 'basic')
        }
        break
      }

      default:
        break
    }
  } catch (err) {
    console.error(`[stripe-webhook] ${event.type} の処理に失敗:`, err)
    return NextResponse.json({ error: 'processing failed' }, { status: 500 })
  }

  return NextResponse.json({ received: true })
}
