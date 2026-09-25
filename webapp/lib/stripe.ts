import Stripe from 'stripe'

let _stripe: Stripe | null = null

// 環境変数未設定でもビルド自体は通るよう、呼び出し時まで初期化を遅延する
export function getStripe(): Stripe {
  if (!_stripe) {
    _stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2026-06-24.dahlia',
    })
  }
  return _stripe
}
