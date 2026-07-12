import { NextResponse } from 'next/server'

export const revalidate = 300

// docs/latest.json(無料枠)をraw.githubusercontent.com経由でサーバー側取得する。
// screener.nobi-labo.comへのCNAME設定によりGitHub PagesのURLは
// https://nobinobi9000.github.io/japan-stock-screener/* への全リクエストを
// screener.nobi-labo.comへ301リダイレクトするため、ブラウザからの直接fetch()は
// CORSエラーで失敗する(リダイレクト元レスポンスにCORSヘッダが無いため)。
// raw.githubusercontent.comはGitHub Pagesの設定に関わらずgitの内容をそのまま返すため、
// 将来ドメインをVercelへ切り替えた後も同じURLで参照できる。
const SOURCE_URL =
  'https://raw.githubusercontent.com/nobinobi9000/japan-stock-screener/main/docs/latest.json'

export async function GET() {
  const res = await fetch(SOURCE_URL, { next: { revalidate: 300 } })
  if (!res.ok) {
    return NextResponse.json({ error: 'upstream fetch failed' }, { status: 502 })
  }
  const data = await res.json()
  return NextResponse.json(data)
}
