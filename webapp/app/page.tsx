import { createClient } from '@/lib/supabase/server'
import { resolvePlan } from '@/lib/entitlement'
import HomeClient from './HomeClient'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const plan = user ? await resolvePlan(supabase, user.id) : 'free'

  return <HomeClient loggedIn={!!user} plan={plan} />
}
