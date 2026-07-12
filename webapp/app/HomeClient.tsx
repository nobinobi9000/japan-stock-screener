'use client'

import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { useScreenerData } from '@/lib/useScreenerData'
import type { Plan } from '@/lib/entitlement'

const INDICATORS = [
  { pt: '15 pt', name: 'MA200 上昇トレンド', desc: '株価がMA200を上回り、かつMA200が直近20日間で上向き。トレンド継続性まで判定。' },
  { pt: '15 pt', name: 'ボリンジャーバンド', desc: '±2σ下限への接触後の反転（BB反発）または+2σ上抜け（BBブレイク）を検出。' },
  { pt: '10 pt', name: '一目均衡表 ① 雲の上', desc: '株価が雲（抵抗帯）の上に位置。中長期的な買い優勢を示す基礎条件。' },
  { pt: '+10 pt', name: '一目均衡表 ② 三役好転', desc: '転換線・基準線・遅行線の3条件が揃う状態。①と合わせ最大20pt。' },
  { pt: '10 pt', name: 'ゴールデンクロス（GC）', desc: 'MA25がMA75を上抜け。短・中期トレンドの転換を示す条件。' },
  { pt: '10 pt', name: '底値クロス', desc: '安値がMA200水準まで押した後に株価がMA200を上抜け。' },
  { pt: '10 pt', name: 'OBV 資金流入', desc: 'On Balance Volumeが上昇トレンド。価格上昇を出来高が支持しているかを確認。' },
  { pt: '10 pt', name: '出来高急増', desc: '直近出来高が30日平均の1.5倍以上。' },
  { pt: '10 pt', name: 'PBR 割安', desc: 'PBR 1.0倍未満で取引されている状態を検出。' },
]

const PATTERNS = [
  { icon: '🚀', name: '強気ブレイク', cond: 'GC + MA200↑ + 出来高急増', desc: 'GC成立直後に出来高急増が重なって成立した状態です。' },
  { icon: '🎯', name: '底打ち反転', cond: '底値クロス + GC + OBV↑', desc: '大底形成後に複数の買い条件が同時に成立した状態です。' },
  { icon: '⛩', name: '一目好転', cond: '一目三役好転', desc: '転換線・基準線・遅行線の3条件が同時に成立した状態です。' },
  { icon: '💎', name: '安定上昇', cond: 'MA200↑ + OBV↑ + BBブレイクなし', desc: 'MA200・OBVがともに上昇基調で、BBブレイクは伴わない状態です。' },
  { icon: '⚡', name: '過熱注意', cond: 'BBブレイク + 出来高急増 + 高スコア', desc: 'BBブレイクと出来高急増が高スコアと同時に成立した状態です。' },
  { icon: '📊', name: 'シグナル点灯', cond: '上記以外の複合シグナル', desc: '上記いずれのパターンにも該当しない、複数シグナル成立銘柄です。' },
]

export default function HomeClient({ loggedIn, plan }: { loggedIn: boolean; plan: Plan }) {
  const router = useRouter()
  const { data, loading, error } = useScreenerData()

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/')
    router.refresh()
  }

  const isPaid = plan === 'basic' || plan === 'premium'

  return (
    <>
      {/* NAV */}
      <nav className="sticky top-0 z-50 h-[52px] flex items-center px-6 gap-4 bg-[rgba(4,8,15,0.85)] backdrop-blur-lg border-b border-[var(--border)]">
        <a href="https://nobi-labo.com" className="font-[family-name:var(--mono)] text-[13px] font-bold text-[var(--green)] tracking-wide">
          nobi-labo
        </a>
        <span className="text-[var(--muted)] text-xs">/</span>
        <span className="text-xs text-[var(--muted)]">japan-stock-screener</span>
        <div className="ml-auto flex items-center gap-4">
          {loggedIn ? (
            <>
              {isPaid && (
                <Link href="/analysis" className="text-xs text-[var(--green)] hover:underline">
                  全銘柄分析へ
                </Link>
              )}
              <button onClick={handleLogout} className="text-xs text-[var(--muted)] hover:text-[var(--text)]">
                ログアウト
              </button>
            </>
          ) : (
            <Link href="/login" className="text-xs text-[var(--green)] hover:underline">
              ログイン
            </Link>
          )}
        </div>
      </nav>

      {/* HERO */}
      <section className="relative z-10 px-6 pt-20 pb-16 max-w-[1100px] mx-auto">
        <div className="inline-flex items-center gap-2 font-[family-name:var(--mono)] text-[10px] font-semibold tracking-[3px] uppercase text-[var(--green)] border border-[var(--border)] px-3.5 py-1 rounded-sm mb-7 bg-[rgba(16,185,129,0.05)]">
          📊 Stock Screener
        </div>
        <h1 className="text-[clamp(32px,6vw,58px)] font-black leading-[1.1] tracking-[-2px] mb-2 text-[var(--head)]">
          日本株の<br />
          <span className="text-[var(--green)]">シグナル</span>を、<br />
          毎日届ける。
        </h1>
        <div className="font-[family-name:var(--mono)] text-[11px] tracking-[4px] text-[var(--muted)] uppercase mb-6">
          Japan Stock Screener · nobi-labo
        </div>
        <p className="text-[15px] text-[#94a3b8] max-w-[520px] leading-loose mb-9">
          東証全銘柄を毎営業日自動スキャン。
          <br />
          9指標×スコアリングで条件成立の事実を検出し、
          <br />
          無料枠は毎日3銘柄、ログインで全銘柄分析を確認できます。
        </p>
        <div className="flex items-center gap-4 flex-wrap mb-14">
          {loggedIn ? (
            isPaid ? (
              <Link
                href="/analysis"
                className="inline-flex items-center gap-2 bg-[var(--green)] text-[#04080f] text-[13px] font-black tracking-wide px-7 py-3.5 rounded-sm hover:opacity-90 transition"
              >
                全銘柄分析へ →
              </Link>
            ) : (
              <span className="text-xs text-[var(--muted)]">
                現在のプラン: free（全銘柄分析はbasic・premiumで利用できます）
              </span>
            )
          ) : (
            <Link
              href="/login"
              className="inline-flex items-center gap-2 bg-[var(--green)] text-[#04080f] text-[13px] font-black tracking-wide px-7 py-3.5 rounded-sm hover:opacity-90 transition"
            >
              ログイン / 新規登録 →
            </Link>
          )}
          <a
            href="#free"
            className="inline-flex items-center gap-2 text-xs text-[var(--muted)] border border-[var(--border2)] px-6 py-3.5 rounded-sm hover:text-[var(--green)] hover:border-[var(--border)] transition"
          >
            無料枠を見る
          </a>
        </div>
      </section>

      {/* 無料枠 */}
      <section id="free" className="relative z-10 px-6 pb-16 max-w-[1100px] mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--green)] uppercase">
            Free — Today&apos;s Top Picks
          </div>
          <div className="flex-1 h-px bg-[var(--border2)]" />
          {data && <div className="font-[family-name:var(--mono)] text-[10px] text-[var(--muted)]">{data.date}</div>}
        </div>

        {loading && <p className="text-sm text-[var(--muted)]">読み込み中...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}

        {data && (
          <>
            {data.market_summary && (
              <div className="bg-[var(--panel)] border border-[var(--border)] border-l-2 border-l-[var(--green)] px-5 py-3.5 rounded-r mb-6 text-[13px] text-[#94a3b8] leading-relaxed">
                💬 {String(data.market_summary.auto_comment ?? '')}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--border2)] border border-[var(--border2)] mb-8">
              {data.top3.map((s, i) => (
                <div key={s.code} className={`bg-[var(--panel)] p-6 ${i === 0 ? 'bg-[#081a10]' : ''}`}>
                  <div className="font-[family-name:var(--mono)] text-[9px] tracking-[2px] text-[var(--muted)] mb-3">
                    RANK <span className="text-[var(--green)]">#{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  <div className="flex items-center gap-2.5 mb-3">
                    <div className="flex-1 h-1 bg-[#1e293b] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[var(--green)] to-[var(--green2)] rounded-full"
                        style={{ width: `${Math.min(s.score, 100)}%` }}
                      />
                    </div>
                    <div className="font-[family-name:var(--mono)] text-base font-bold text-[var(--green)]">
                      {s.score}
                    </div>
                  </div>
                  <div className="text-sm font-bold text-[var(--head)] mb-1">{s.name}</div>
                  <div className="font-[family-name:var(--mono)] text-[10px] text-[var(--muted)] mb-3">
                    {s.code} · {s.sector} · ¥{s.price?.toLocaleString() ?? '—'} · {s.risk_tag}
                  </div>
                  <span className="inline-block text-[11px] font-bold px-2.5 py-1 rounded-sm bg-[rgba(16,185,129,0.1)] border border-[var(--border)] text-[var(--green)]">
                    {s.pattern}
                  </span>
                </div>
              ))}
            </div>

            {data.sector_heatmap.length > 0 && (
              <div className="bg-[var(--panel)] border border-[var(--border2)] rounded-xl p-4">
                <h3 className="text-sm font-semibold text-[var(--head)] mb-3">セクター別平均スコア</h3>
                <div className="space-y-2">
                  {data.sector_heatmap.slice(0, 8).map((sec) => (
                    <div key={sec.name} className="flex items-center gap-3 text-xs">
                      <span className="w-32 shrink-0 text-[var(--text)] truncate">{sec.name}</span>
                      <div className="flex-1 h-2 bg-[var(--panel2)] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[var(--green)] rounded-full"
                          style={{ width: `${Math.min(sec.avg_score, 100)}%` }}
                        />
                      </div>
                      <span className="w-16 shrink-0 text-right text-[var(--green2)]">{sec.avg_score.toFixed(1)}</span>
                      <span className="w-14 shrink-0 text-right text-[var(--muted)]">{sec.stock_count}銘柄</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {/* プラン */}
      <section className="relative z-10 px-6 py-16 max-w-[1100px] mx-auto border-t border-[var(--border2)]">
        <div className="flex items-center gap-4 mb-6">
          <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--green)] uppercase">
            Plans
          </div>
          <div className="flex-1 h-px bg-[var(--border2)]" />
          <div className="font-[family-name:var(--mono)] text-[10px] text-[var(--muted)]">βテスト期間中は全機能無料</div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--border2)] border border-[var(--border2)]">
          <div className="bg-[var(--panel)] p-8">
            <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--muted)] uppercase mb-4">Free</div>
            <div className="text-lg font-black mb-5 text-[var(--head)]">無料プラン</div>
            <div className="font-[family-name:var(--mono)] text-[32px] font-bold text-[var(--text)] mb-6">¥0</div>
            <div className="h-px bg-[var(--border2)] mb-5" />
            <ul className="flex flex-col gap-2.5 mb-7 text-xs text-[#94a3b8]">
              <li>厳選3銘柄を毎日表示</li>
              <li>セクター別平均スコア</li>
              <li>Discord #daily-picks</li>
              <li className="text-[#1e293b]">全銘柄分析</li>
              <li className="text-[#1e293b]">指標スコア内訳</li>
            </ul>
            {!loggedIn && (
              <Link href="/login" className="block w-full py-3 text-center text-xs font-black tracking-wide rounded-sm border border-[var(--border2)] text-[var(--muted)] hover:text-[var(--text)] hover:border-[var(--border)] transition">
                ログイン / 新規登録
              </Link>
            )}
          </div>

          <div className="bg-[#070f18] p-8 relative">
            <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--green)] uppercase mb-4">
              Basic — β公開中 全機能無料
            </div>
            <div className="text-lg font-black mb-5 text-[var(--head)]">ベーシック</div>
            <div className="font-[family-name:var(--mono)] text-[32px] font-bold text-[var(--green)] mb-1">
              ¥980<small className="text-xs font-normal text-[var(--muted)]"> /月</small>
            </div>
            <div className="text-[11px] text-[var(--green)] font-bold mb-6 min-h-4">βテスト期間中は全機能を無料提供中</div>
            <div className="h-px bg-[var(--border2)] mb-5" />
            <ul className="flex flex-col gap-2.5 mb-7 text-xs text-[#94a3b8]">
              <li>厳選3銘柄を毎日表示</li>
              <li>当日分 全銘柄分析ページ</li>
              <li>ソート・検索・フィルター</li>
              <li>全指標スコア内訳</li>
              <li>Discord #full-report</li>
            </ul>
            {isPaid ? (
              <Link href="/analysis" className="block w-full py-3 text-center text-xs font-black tracking-wide rounded-sm bg-[var(--green)] text-[#04080f] hover:opacity-90 transition">
                全銘柄分析へ →
              </Link>
            ) : (
              <Link href="/login" className="block w-full py-3 text-center text-xs font-black tracking-wide rounded-sm bg-[var(--green)] text-[#04080f] hover:opacity-90 transition">
                ログイン / 新規登録 →
              </Link>
            )}
          </div>

          <div className="bg-[var(--panel)] p-8">
            <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--muted)] uppercase mb-4">Premium</div>
            <div className="text-lg font-black mb-5 text-[var(--head)]">プレミアム</div>
            <div className="font-[family-name:var(--mono)] text-[32px] font-bold text-[var(--green)] mb-1">
              ¥1,980<small className="text-xs font-normal text-[var(--muted)]"> /月</small>
            </div>
            <div className="text-[11px] text-[var(--muted)] font-bold mb-6 min-h-4">準備中</div>
            <div className="h-px bg-[var(--border2)] mb-5" />
            <ul className="flex flex-col gap-2.5 mb-7 text-xs text-[#94a3b8]">
              <li>Basicの全機能</li>
              <li className="text-[#1e293b]">30日分レポートアーカイブ</li>
              <li className="text-[#1e293b]">シグナル発生履歴</li>
            </ul>
            <span className="block w-full py-3 text-center text-xs font-black tracking-wide rounded-sm border border-[#1e293b] text-[#1e293b]">
              近日公開
            </span>
          </div>
        </div>
      </section>

      {/* 指標一覧 */}
      <section className="relative z-10 px-6 py-16 max-w-[1100px] mx-auto border-t border-[var(--border2)]">
        <div className="flex items-center gap-4 mb-6">
          <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--green)] uppercase">
            Score Indicators — 9指標 合計100点
          </div>
          <div className="flex-1 h-px bg-[var(--border2)]" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--border2)] border border-[var(--border2)]">
          {INDICATORS.map((ind) => (
            <div key={ind.name} className="bg-[var(--panel)] p-5 flex gap-4 items-start hover:bg-[var(--panel2)] transition">
              <div className="font-[family-name:var(--mono)] text-[11px] font-bold text-[var(--green)] border border-[var(--border)] px-2 py-0.5 whitespace-nowrap min-w-[52px] text-center shrink-0">
                {ind.pt}
              </div>
              <div>
                <div className="text-[13px] font-bold mb-1 text-[var(--text)]">{ind.name}</div>
                <div className="text-[11px] text-[var(--muted)] leading-relaxed">{ind.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* パターン分類 */}
      <section className="relative z-10 px-6 py-16 max-w-[1100px] mx-auto border-t border-[var(--border2)]">
        <div className="flex items-center gap-4 mb-6">
          <div className="font-[family-name:var(--mono)] text-[9px] font-bold tracking-[3px] text-[var(--green)] uppercase">
            Signal Patterns — 6種類の自動分類
          </div>
          <div className="flex-1 h-px bg-[var(--border2)]" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--border2)] border border-[var(--border2)]">
          {PATTERNS.map((p) => (
            <div key={p.name} className="bg-[var(--panel)] p-6 hover:bg-[var(--panel2)] transition">
              <div className="text-[22px] mb-2.5 leading-none">{p.icon}</div>
              <div className="text-sm font-black mb-1.5 text-[var(--head)]">{p.name}</div>
              <div className="font-[family-name:var(--mono)] text-[10px] text-[var(--green)] mb-2">{p.cond}</div>
              <div className="text-[11px] text-[var(--muted)] leading-relaxed">{p.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 px-6 py-24 text-center border-t border-[var(--border2)]">
        <div className="max-w-[560px] mx-auto">
          <div className="text-[clamp(28px,5vw,44px)] font-black tracking-[-1.5px] mb-4 text-[var(--head)]">
            今日から<span className="text-[var(--green)]">無料</span>で始める
          </div>
          <p className="text-sm text-[var(--muted)] mb-9 leading-loose">
            無料枠はログイン不要・即利用可能。
            <br />
            ベーシックプランはβテスト期間中、全機能を無料提供中。
          </p>
          {!loggedIn && (
            <Link
              href="/login"
              className="inline-flex items-center gap-2 bg-[var(--green)] text-[#04080f] text-[13px] font-black tracking-wide px-7 py-3.5 rounded-sm hover:opacity-90 transition"
            >
              ログイン / 新規登録 →
            </Link>
          )}
          <p className="mt-5 text-[10px] text-[#1e293b]">
            ※ 本サービスは条件成立の事実表示のみを行い、投資助言は行いません。投資判断はご自身の責任でお願いします。
          </p>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="relative z-10 border-t border-[var(--border2)] px-6 py-6">
        <div className="max-w-[1100px] mx-auto flex items-center justify-between gap-3 flex-wrap">
          <a href="https://nobi-labo.com" className="font-[family-name:var(--mono)] text-xs font-bold text-[var(--green)]">
            nobi-labo
          </a>
          <div className="flex gap-5">
            <a href="https://nobinobi9000.github.io/japan-stock-screener/legal/terms.html" className="text-[11px] text-[#1e293b] hover:text-[var(--muted)] transition">
              利用規約
            </a>
            <a href="https://nobinobi9000.github.io/japan-stock-screener/legal/disclaimer.html" className="text-[11px] text-[#1e293b] hover:text-[var(--muted)] transition">
              免責事項
            </a>
            <a href="https://nobinobi9000.github.io/japan-stock-screener/legal/privacy.html" className="text-[11px] text-[#1e293b] hover:text-[var(--muted)] transition">
              プライバシーポリシー
            </a>
            <a href="https://nobinobi9000.github.io/japan-stock-screener/legal/tokushoho.html" className="text-[11px] text-[#1e293b] hover:text-[var(--muted)] transition">
              特定商取引法に基づく表記
            </a>
          </div>
          <span className="font-[family-name:var(--mono)] text-[11px] text-[#1e293b]">© 2026 nobi-labo</span>
        </div>
      </footer>
    </>
  )
}
