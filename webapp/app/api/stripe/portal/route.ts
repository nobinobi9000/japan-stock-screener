import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { getStripe } from '@/lib/stripe'

export async function POST(request: Request) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const admin = createAdminClient()
  const { data: identity } = await admin
    .from('account_external_identities')
    .select('external_id')
    .eq('user_id', user.id)
    .eq('provider', 'stripe')
    .maybeSingle()

  if (!identity?.external_id) {
    return NextResponse.json({ error: 'no stripe customer found' }, { status: 404 })
  }

  const origin = new URL(request.url).origin
  const session = await getStripe().billingPortal.sessions.create({
    customer: identity.external_id,
    return_url: `${origin}/`,
  })

  return NextResponse.json({ url: session.url })
}
