import { createClient } from '@supabase/supabase-js'

// service_roleキーでRLSを越えて書き込む管理者クライアント。
// Stripe webhookなど、ユーザーセッションを介さないサーバー側処理専用。
// SUPABASE_SERVICE_ROLE_KEYはNEXT_PUBLIC_を付けず、Vercelのサーバー側環境変数としてのみ設定する。
export function createAdminClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )
}
