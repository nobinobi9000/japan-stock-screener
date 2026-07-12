import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const supabase = await createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const dateParam = request.nextUrl.searchParams.get('date')
  const functionUrl = new URL(
    `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/screener-snapshot`
  )
  if (dateParam) {
    functionUrl.searchParams.set('date', dateParam)
  }

  const res = await fetch(functionUrl, {
    headers: {
      Authorization: `Bearer ${session.access_token}`,
    },
    cache: 'no-store',
  })

  const body = await res.json()
  return NextResponse.json(body, { status: res.status })
}
